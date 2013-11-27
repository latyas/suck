import shlex
import sys
from string import Template
import re

# notes:
'''
FINAL MEMORY ADMINISTRATION: (NOT FINISHED)

data: 

_heap dw 256 dup (0)
_hp dw 0

var organized form:
	'VAR NAME':(TYPE,start_position)


def malloc():
	[heap+hp] = data
	hp += len(data) -> calculated
	return offset of _heap

the offset of the resource stores in a dict, the key is the name of resource.
when we reference the resource, denotation of the resource will be replaced to heap[OFFSET] 

CHANGES LOG:
2013-11-26 deleted decorator from key_operator 
2013-11-27 array achieved

Tips:
1. key_for need rewrite (for arguments should call key_statement() instead of handling inside)
2. achieving evaluation of local statements 
3. key_operator  if _heap in source -> do not find in resource dict
4. dereference -> ([_heap+offset],length)

'''

if len(sys.argv) != 2:
    print 'Please specify one filename on the command line.'
    sys.exit(1)

filename = sys.argv[1]
body = file(filename, 'rt').read()
lex = shlex.shlex(body)
lex.commenters = '//'

#CODES
_generator_counter = 0
_segment_data = ''
_segment_code = ''
_segment_stack = '''
dw 128 dup (0)
'''
_function_codes = ''
_hp = 0 #increase 1 = 1 byte
_tmp = {'for_id':[]}
_labels = []

def local_statement_lexer(body):
	local_lex = shlex.shlex(body)
	local_lex.commenters = '//'
	return local_lex
def local_statement(body): #END with ;
	print 'Local_statement_start'
	_local_lexer = local_statement_lexer(body)
	while True:
		#foo = _local_lexer.get_token()
		#print 'local:',foo
		foo = key_statement(_local_lexer)
		if foo == ';' or foo == None:
			break
	print 'Local_statement_end'

def gen_function_code(funcname,codes):
	from string import Template
	foo = """
	$FUNCTION proc
		$CODES
		ret
	endp
	"""
	bar = Template(foo)
	return bar.substitude({'FUNCTION':funcname,'CODES':codes})

def counter():
	global _generator_counter
	_generator_counter += 1

def get_counter():
	global _generator_counter
	return _generator_counter

def add_code(text):
	global _segment_code
	_segment_code += text + '\n'
	counter()

def add_data(text):
	global _segment_data
	_segment_data += text + '\n'
	counter()

def _push_for_id():
	global _tmp
	_tmp['for_id'].append(get_counter())

def _pop_for_id():
	global _tmp
	return _tmp['for_id'].pop()

def _get_for_id():
	global _tmp
	return _tmp['for_id'][-1]

def _push_label(label):
	global _labels
	_labels.append(label)

def _pop_label():
	global _labels
	return _labels.pop()

def push(value,length):
	global lexer_resource
	pattern = '''
;push to user stack
push bx
push dx
mov bx,[_user_stack_ptr]
mov dx,$SOURCE
mov [bx],dx
add _user_stack_ptr,$LENGTH
pop dx
pop bx
;push END
		'''

	if '[_heap' in value:
		source = value
	else:
		try:
			int(value)
			source = value
		except:
			source = '[_heap+' + str(lexer_resource[value][1]) + ']' 
	codes = Template(pattern).substitute({'SOURCE':source,'LENGTH':length})
	add_code(codes)
	
def pop(dest,length):
	pattern = '''
;pop to dest
push ax
push bx
mov bx,[_user_stack_ptr]
mov $REG,[bx-$LENGTH]
mov $DEST,$REG
sub _user_stack_ptr,$LENGTH
pop bx
pop ax
;pop END
		'''

	if length == 1:
		reg = 'al'
		prefix = 'BYTE PTR'
	else:
		prefix = 'WORD PTR'
		reg = 'ax'


	add_code(Template(pattern).substitute({'PREFIX':prefix,'REG':reg,'DEST':dest,'LENGTH':length}))


def add_func(text):
	pass
def output():
	global _segment_data,_segment_code,_segment_stack
	print 'data segment'
	print '\t_heap dw 32768 dup (0)'
	print '\t_hp dw 0'
	print '\t_buffer dw 4096 dup (0)'
	print '\t_user_stack dw 4096 dup (0)'
	print '\t_user_stack_ptr dw 0'
	print '\t',
	print _segment_data.replace('\n','\n\t')
	print 'ends'

	print 'stack segment'
	print '\t',
	print _segment_stack.replace('\n','\n\t')
	print 'ends'

	print 'code segment'
	print """
start:
	; set segment registers:
	mov ax, data
	mov ds, ax
	mov es, ax

	;initiate _hp , _user_stack_ptr
	mov _hp,offset _heap
	mov _user_stack_ptr,offset _user_stack
	"""
	print _segment_code.replace('\n','\n\t')
	print """
	; wait for any key....    
	mov ah, 1
	int 21h

	mov ax, 4c00h ; exit to operating system.
	int 21h
      
	"""
	#FUNCTION CODES SECTION
	print '\t',_function_codes
	print 'ends'
	print
	print 'end start'



# DECORATOR
def keyword_decorator(lexer):
	def _kd(func):
		def __kd(*arg):
			func(lexer,arg)
		return __kd
	return _kd


def function_decorator(lexer):
	def _fd(func):
		def __fd(*arg):
			func(lexer,arg)
		return __fd
	return _fd

# USER_DEFINE_FUNCTIONS
@function_decorator(lex)
def _func_printf(lexer,param):
	global _segment_data
	string_data = param[0]
	string_data = string_data.replace('\\n','",13,10,"') # \n -> \r\n
	string_label = 'STRING_'+str(get_counter())
	add_code('''
push dx
lea dx,%s
mov ah,9
int 21h
pop dx
	''' % string_label)
	add_data('%s db %s,"$"' % (string_label,string_data))
	
	counter()


@function_decorator(lex)
def _func_puts(lexer,param):
	string_data = param[0]
	string_data = string_data[:-1] + '\\n' + '"'
	_func_printf(string_data)


# 
@keyword_decorator(lex)
def key_for(lexer,arg):
	# tips:
	# use _func_reference(keyword) to access heap 
	#
	#
	#
	'''
	Pairs:
	1. 	i=0 --> mov cx,0
		i=X --> mov cx,X
	2. 	i<=N --> cmp cx,N; jle LOOP_START
		i<N --> cmp cx,N; jl LOOP_START
		i>=N --> cmp cx,N; jge LOOP_START
		i>N --> cmp cx,N; jg LOOP_START
	3. 	i++ --> inc cx
		i-- --> dec cx
		i+=N --> add cx,N
		i-=N --> sub cx,N
		i*=N --> 
				 push ax
				 push dx
				 mov ax,cx
				 mov dl,N
				 mul dl
				 mov cx,ax
				 pop dx
				 pop ax

		i/=N --> 
				 push ax
				 push dx
				 mov ax,cx
				 mov dl,N
				 div dl
				 xor ah,ah
				 mov cx,ax
				 pop dx
				 pop ax
		i%=N --> 
				 push ax
				 push dx
				 mov ax,cx
				 mov dl,N
				 div dl
				 mov al,ah
				 xor ah,ah
				 mov cx,ax
				 pop dx
				 pop ax
		i<<=N --> 
				 SHL cx,N
		i>>N --> 
				 SHR cx,N
	'''
	bar = lexer.get_token()
	if bar != '(':
		print 'ERROR'
		sys.exit(0)
	else:
		iterator = lexer.get_token()
		lexer.push_token(iterator)
		_push_for_id()
		

		
		# handles dependent
		arguments = '' 
		while True:
			foo = lexer.get_token()
			if foo == ')':
				break
			arguments += foo + ' '


		arguments = arguments.split(';')

		# if define a iterator in for 
		token = arguments[0].split(' ')[0]
		if token in lexer_keywords:
			new_codes = token + ' ' + arguments[0].split(' ')[1] + ';'
			new_codes += arguments[0].replace(token + ' ','')
			local_statement(new_codes)
		else:
			local_statement(arguments[0] + ';') #initiate
		add_code('LOOP_FOR_%s:' % _get_for_id())
		while True:
			foobar = key_statement(lexer)
			if foobar == '}':
				break
		print 'WTF',arguments[2]+';'
		local_statement(arguments[2]+ ';')
		_push_label('LOOP_FOR_%s:' % _get_for_id())
		local_statement(arguments[1]+ ';')	#jump	

		add_code('LOOP_FOR_%s_END:' % _pop_for_id())
		#sys.exit(0)
		# initiate iterator


@keyword_decorator(lex)
def key_assembly(lexer,arg):
	bar = lexer.get_token() # remove {
	if bar != '{':
		print 'ERROR'
		sys.exit(0)
	else:
		# context
		foo = ''
		temp_counter = 0
		while True:
			bar = lexer.get_token()
			if bar == '}' :
				break
			if temp_counter == 0:
				foo += bar + ' '
			else:
				foo += bar
			temp_counter += 1
			if bar == ';':
				temp_counter = 0

		foo = foo.split(';')
		for i in foo:
			add_code(i)

def _get_type_bytes(tp):
	digits = {'BYTE':1,
			  'WORD':2,
			  'DWORD':4}
	return digits[tp]


def key_malloc(lexer,*arg):
	global lexer_resource,_hp
	#TEST pointer and array

	# if pointer ?
	pointer = False
	foo = lexer.get_token()
	if foo == '*':
		pointer = True
	else:
		lexer.push_token(foo)

	# get var name
	var = lexer.get_token()
	foo = lexer.get_token()
	# if array
	if foo == '[':
		array_size = int(lexer.get_token())
		lexer_resource[var] = (arg[0],_hp,True)
		_hp += _get_type_bytes(arg[0]) * array_size
		lexer.get_token()
		print '[MALLOC] ARRAY',arg[0],var,lexer_resource[var],array_size,_hp - _get_type_bytes(arg[0]) * array_size
	else:		
		lexer.push_token(foo)
		lexer_resource[var] = (arg[0],_hp,pointer)
		_hp += _get_type_bytes(arg[0])
		print '[MALLOC] ',arg[0],var,lexer_resource[var]
	foo = lexer.get_token()
	if foo != ';':
		print 'MALLOC SYNTAX ERROR',foo
		sys.exit(0)
	# allocating
	# format of resource dict: (TYPE,HEAP_OFFSET,POINTER)


	



@keyword_decorator(lex)
def key_free(lexer,arg):
	# lazy free, just delete key from dict
	global lexer_resource
	pass

def key_operator(lexer,*arg):
	global lexer_keywords,lexer_resource
	# lazy free, just delete key from dict
	print 'DEBUG',arg
	opt = arg[0]
	source = arg[1]

	def _get_resource(target):
		#returns (referencable obj,obj type)
		if '[_heap' in target:
			foo = target.split(',') # 0:pointer , 1.resource name
			_type = lexer_resource[foo[1]][0]
			return (foo[0],_type)
		else:
			ptr = '[_heap+' + str(lexer_resource[target][1])  + ']'
			_type = lexer_resource[target][0]
			return (ptr,_type)

	def _get_next():
		if len(arg) == 3: #arg = (operator,source,dest)
			return arg[2]
		else:
			return lexer.get_token()

	def _reference():
		offset = lexer.get_token()
		lexer.get_token() # remove ]
		pointer = lexer_resource[source][1]
		return '[_heap+%s]' % str(int(pointer)+int(offset)) +',%s' % source


	# + or ++ / - or --
	# < or <= / > or >=
	# X or X= 
	def _less():
		immediate_num = True
		#another = lexer.get_token()
		another = _get_next()
		try:
			int(another)
		except:
			immediate_num = False
		# source + another
		reg_type = _get_resource(source)[1]

		if reg_type == 'BYTE':
			reg_type = 'al'
		else:
			reg_type = 'ax'

		if immediate_num == False:	
			if _get_resource(source)[1] != _get_resource(another)[1]:
				if _get_type_bytes(_get_resource(source)[1]) < _get_type_bytes(_get_resource(another)[1]):
					reg_type = _get_resource(another)[1]			
			pattern = '''
;_less $CMPER < $OPERATOR
push ax
mov ax,$CMPER
cmp $REG,$CMPER
jl $LABEL
pop ax
;less cmp end
		'''
			codes = Template(pattern).substitute({'CMPER':_get_resource(source)[0] , 'REG':reg_type,'OPERATOR':another,'LABEL':_pop_label()})
		else:
			pattern = '''
;_less $REG < $OPERATOR
push ax
mov ax,$CMPER
cmp $REG,$OPERATOR
jl $LABEL
pop ax
;less cmp end
		'''
			codes = Template(pattern).substitute({'CMPER':_get_resource(source)[0] , 'REG':reg_type,'OPERATOR':another,'LABEL':_pop_label()})

		add_code(codes)
	def _assign():
		# Unary
		# evaluate right value
		# right value is read from buffer[0] ---->
		reg_type = _get_resource(source)[1]
		if reg_type == 'BYTE':
			reg_type = 'dl'
			prefix = 'BYTE PTR'
		else:
			prefix = 'WORD PTR'
			reg_type = 'dx'
		print 'ASSIGN'
		key_statement(lexer)
		print 'ASSIGN - END'
		pop('dx',2)
		# right value evaluated
		pattern = '''
;assign $VAR
mov $SOURCE,$REG
;end assign
		''' 
		codes = Template(pattern).substitute({'VAR':source,'REG':reg_type,'SOURCE':_get_resource(source)[0]})

		add_code(codes)
	def _plus():
		# Binary
		immediate_num = True
		#another = lexer.get_token()
		another = _get_next()
		try:
			int(another)
		except:
			immediate_num = False

		
		# source + another
		reg_type = _get_resource(source)[1]

		if reg_type == 'BYTE':
			reg_type = 'al'
		else:
			reg_type = 'ax'

		if immediate_num == False:	
			if _get_resource(source)[1] != _get_resource(another)[1]:
				if _get_type_bytes(_get_resource(source)[1]) < _get_type_bytes(_get_resource(another)[1]):
					reg_type = _get_resource(another)[1]	

			# DWORD is ignored for now ..
			pattern = '''
;add two number ($VAR_1 + $VAR_2)
push bx
push ax

lea bx,_heap
xor ax,ax
;first number
mov $REG,$FIRST
add $REG,$SECOND
lea bx,_buffer
mov [bx],$REG
pop ax
pop bx
;end add
	'''
			codes = Template(pattern).substitute({'VAR_1':source,'VAR_2':another,'REG':reg_type,'FIRST':_get_resource(source)[0],'SECOND':_get_resource(another)[0]})
		else:
			pattern = '''
;add two number
push bx
push ax

lea bx,_heap
xor ax,ax
;first number
mov $REG,$FIRST
add $REG,$SECOND
lea bx,_buffer
mov [bx],$REG
pop ax
pop bx
;end add
	'''
			codes = Template(pattern).substitute({'REG':reg_type,'FIRST':_get_resource(source)[0],'SECOND':another})

		add_code(codes)

	def _plusplus():
		reg_type = _get_resource(source)[1]
		ptr = lexer_resource[source][2]


		if ptr:
			if reg_type == 'BYTE':
				op = 'inc %s' % str(_get_resource(source)[0])
			else:
				op = 'add '  + str(_get_resource(source)[0]) + ', 2'
		else:
			op = 'inc %s' % str(_get_resource(source)[0])

		codes = op

		add_code(codes)


	# ******************************

	opt_method = {'=':_assign,
				  '+':_plus,
				  '<':_less,
				  '++':_plusplus,
				  '[':_reference}
	
	# OPT is certain 
	if len(arg) != 3:
		foo = lexer.get_token()
		if opt+foo in opt_method:
			bar = opt + foo
			try:
				opt_method[bar]
				opt += foo

				foo2 = lexer.get_token() # <<= >>= 
				barbar = bar + foo2
				try:
					opt_method[barbar]
					#3 chars
					foo += foo2
				except:
					#not in opt_method
					lexer.push_token(foo2)

			except:
				# not in opt_method
				lexer.push_token(foo)
				foo = ''
				
		else:
			lexer.push_token(foo)
	else:
		opt = arg[0]

	print 'opt',opt

	if '[_heap' not in source:
		try:
			lexer_resource[source]
		except:
			print '[VARERROR] variant hasn\'t assigned.',source
			sys.exit(9)

	try:
		lexer_keywords[opt]
	except:
		print '[operator] invalid',opt
		sys.exit(9)

	return opt_method[opt]()
	#START
	'''
	  '+':key_operator,
	  '-':key_operator,
	  '++':key_operator,
	  '--':key_operator,
	  '*':key_operator,
	  '/':key_operator,
	  '%':key_operator,
	  '+=':key_operator,
	  '-=':key_operator,
	  '*=':key_operator,
	  '/=':key_operator,
	  '%=':key_operator,
	  '>>':key_operator,
	  '<<':key_operator,
	  '<<=':key_operator,
	  '>>=':key_operator
	'''


	


def key_function_call(lexer,func):
	bar = lexer.get_token()
	params = ''
	while bar != ')': #commit that if it is a function call, final char of params is ')'
		params += bar			
		bar = lexer.get_token()
	lexer.get_token() # remove ';'
	#CALL FUNCTION
	lexer_function[func](params,func)


def key_statement(lexer,*arg):
	global lexer_keywords
	#normal statement processing function
	if len(arg) == 0:
		statement = lexer.get_token()
	else:
		statement = arg[0]


	print 'statement',statement
	if statement == '':
		return None
	if statement == 'main':
		lexer.get_token() # (
		lexer.get_token() # )
		lexer.get_token() # {
		statement = lexer.get_token() # get next statement
	
	# if statement = "}" ---> END
	if statement == '}':
		return '}'
	if statement == ')':
		return ')'
	if statement == '{':
		return '{'
	if statement == ';':
		# END
		return None
	
	if statement in lexer_keywords.keys():
		lexer_keywords[statement](lexer,statement) # call keyword function
	else:
		# not keyword, read until ';'
		operator = lexer.get_token()
		if operator == ';': # immediate number
			# END
			push(statement,2)
			return statement

		#FUNCTION CALL	
		if operator == '(':
			key_function_call(lexer,statement)
		else:
			ret = key_operator(lexer,operator,statement)
			if ret != None:
				print 'HAS RET:',ret
				key_statement(lexer,ret)
			return None

	return None



lexer_resource = {}
lexer_function = {'printf':_func_printf,
				  'puts':_func_puts}
lexer_keywords = {'for':key_for,
			      'assembly':key_assembly,
			      'BYTE':key_malloc,
			      'WORD':key_malloc,
			      'DWORD':key_malloc,
			      '=':key_operator,
			      '[':key_operator,
			      '<':key_operator,
			      '>':key_operator,
			      '<=':key_operator,
			      '>=':key_operator,
			      '+':key_operator,
			      '-':key_operator,
			      '++':key_operator,
			      '--':key_operator,
			      '*':key_operator,
			      '/':key_operator,
			      '%':key_operator,
			      '+=':key_operator,
			      '-=':key_operator,
			      '*=':key_operator,
			      '/=':key_operator,
			      '%=':key_operator,
			      '>>':key_operator,
			      '<<':key_operator,
			      '<<=':key_operator,
			      '>>=':key_operator}


while True:
	ret = key_statement(lex)
	if ret == '}':
		break


output()
print lexer_resource
'''
for token in lexer:
    print token
'''