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

the offset of the resource stores in a dict, the name of resource is the key.
when we reference the resource, denotation of the resource will be replaced to heap[OFFSET] 


Tips:
1. key_for need rewrite (for arguments should call key_statement() instead of handling inside)

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

def add_func(text):
	pass
def output():
	global _segment_data,_segment_code,_segment_stack
	print 'data segment'
	print '\t_heap dw 512 dup (0)'
	print '\t_hp dw 0'
	print '\t_buffer dw 128 dup (0)'
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
			arguments += foo
		arguments = arguments.split(';')

		pattern = re.compile('([\+\-\=\>\<]?)')

		opt_foo = ''.join(pattern.findall(arguments[0]))
		dest = arguments[0].replace(iterator+opt_foo,'')
		print (opt_foo,iterator,dest)
		key_operator(opt_foo,iterator,dest)
		add_code('LOOP_FOR_%s:' % _get_for_id())
		while True:
			foobar = key_statement(lexer)
			if foobar == '}':
				break

		#bound check
		opt_foo = ''.join(pattern.findall(arguments[2]))
		dest = arguments[2].replace(iterator+opt_foo,'')
		print (opt_foo,iterator,dest)
		key_operator(opt_foo,iterator,dest)

		# iterating
		opt_foo = ''.join(pattern.findall(arguments[1]))
		dest = arguments[1].replace(iterator+opt_foo,'')
		print (opt_foo,iterator,dest)
		key_operator(opt_foo,iterator,dest)



		_pop_for_id()
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

@keyword_decorator(lex)
def key_malloc(lexer,arg):
	global lexer_resource,_hp

	# get var name
	var = lexer.get_token()
	foo = lexer.get_token()
	if foo != ';':
		print 'MALLOC SYNTAX ERROR'
		sys.exit(0)
	# allocating
	lexer_resource[var] = (arg[0],_hp)
	_hp += _get_type_bytes(arg[0])

	print '[MALLOC]',arg[0],var,lexer_resource[var]



@keyword_decorator(lex)
def key_free(lexer,arg):
	# lazy free, just delete key from dict
	global lexer_resource
	pass

@keyword_decorator(lex)
def key_operator(lexer,arg):
	global lexer_keywords,lexer_resource
	# lazy free, just delete key from dict

	opt = arg[0]
	source = arg[1]


	def _get_next():
		if len(arg) == 3: #arg = (operator,source,dest)
			return arg[2]
		else:
			return lexer.get_token()
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
		reg_type = lexer_resource[source][0]

		if reg_type == 'BYTE':
			reg_type = 'al'
		else:
			reg_type = 'ax'

		if immediate_num == False:	
			if lexer_resource[source][0] != lexer_resource[another][0]:
				if _get_type_bytes(lexer_resource[source][0]) < _get_type_bytes(lexer_resource[another][0]):
					reg_type = lexer_resource[another][0]			
			pattern = '''
;_less $CMPER < $OPERATOR
push ax
mov ax,$CMPER
cmp $REG,$CMPER
jl $LABEL
pop ax
;less cmp end
		'''
			codes = Template(pattern).substitute({'CMPER':'[_heap+'+str(lexer_resource[source][1])+']' , 'REG':reg_type,'OPERATOR':another,'LABEL':'LOOP_FOR_%s' % _get_for_id()})
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
			codes = Template(pattern).substitute({'CMPER':'[_heap+'+str(lexer_resource[source][1])+']' , 'REG':reg_type,'OPERATOR':another,'LABEL':'LOOP_FOR_%s' % _get_for_id()})

		add_code(codes)
	def _assign():
		# Unary
		# evaluate right value
		# right value is read from buffer[0] ---->
		reg_type = lexer_resource[source][0]
		if reg_type == 'BYTE':
			reg_type = 'dl'
		else:
			reg_type = 'dx'
		key_statement(lexer)
		# right value evaluated
		pattern = '''
;assign $VAR
push bx
push dx
lea bx,_buffer
mov $REG,[bx]
lea bx,_heap
mov [bx+$SOURCE],$REG
pop dx
pop bx
;end assign
		''' 
		codes = Template(pattern).substitute({'VAR':source,'REG':reg_type,'SOURCE':lexer_resource[source][1]})

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
		reg_type = lexer_resource[source][0]

		if reg_type == 'BYTE':
			reg_type = 'al'
		else:
			reg_type = 'ax'

		if immediate_num == False:	
			if lexer_resource[source][0] != lexer_resource[another][0]:
				if _get_type_bytes(lexer_resource[source][0]) < _get_type_bytes(lexer_resource[another][0]):
					reg_type = lexer_resource[another][0]

			# DWORD is ignored for now ..
			pattern = '''
;add two number ($VAR_1 + $VAR_2)
push bx
push ax

lea bx,_heap
xor ax,ax
;first number
mov $REG,[bx+$FIRST]
add $REG,[bx+$SECOND]
lea bx,_buffer
mov [bx],$REG
pop ax
pop bx
;end add
	'''
			codes = Template(pattern).substitute({'VAR_1':source,'VAR_2':another,'REG':reg_type,'FIRST':lexer_resource[source][1],'SECOND':lexer_resource[another][1]})
		else:
			pattern = '''
;add two number
push bx
push ax

lea bx,_heap
xor ax,ax
;first number
mov $REG,[bx+$FIRST]
add $REG,$SECOND
lea bx,_buffer
mov [bx],$REG
pop ax
pop bx
;end add
	'''
			codes = Template(pattern).substitute({'REG':reg_type,'FIRST':lexer_resource[source][1],'SECOND':another})

		add_code(codes)

	def _plusplus():
		reg_type = lexer_resource[source][0]

		if reg_type == 'BYTE':
			op = 'inc %s' % '[_heap+'+str(lexer_resource[source][1]) + ']'
		else:
			op = 'add '  + '[_heap+'+ str(lexer_resource[source][1]) + ']' + ', 2'

		codes = op

		add_code(codes)


	# ******************************

	opt_method = {'=':_assign,
				  '+':_plus,
				  '<':_less,
				  '++':_plusplus}
	
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

	opt_method[opt]()
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


def key_statement(lexer):
	global lexer_keywords
	#normal statement processing function
	statement = lexer.get_token()
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
		lexer_keywords[statement](statement) # call keyword function
	else:
		# not keyword, read until ';'
		operator = lexer.get_token()
		if operator == ';':
			# END
			return statement

		#FUNCTION CALL	
		if operator == '(':
			key_function_call(lexer,statement)
		else:
			key_operator(operator,statement)
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

'''
for token in lexer:
    print token
'''