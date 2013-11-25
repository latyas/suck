import shlex
import sys
from string import Template

# notes:
'''
FINAL MEMORY ADMINISTRATION: (NOT FINISHED)

data: 

_heap db 256 dup (0)
_hp db 0

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

def add_func(text):
	pass
def output():
	global _segment_data,_segment_code,_segment_stack
	print 'data segment'
	print '\t_heap db 512 dup (0)'
	print '\t_hp db 0'
	print '\t_buffer db 128 dup (0)'
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
		params_list = ''
		bar = lexer.get_token() #i OPT ?
		while bar != ')':
			params_list += bar			
			bar = lexer.get_token()
		
		params_list = params_list.split(';')

		#params_list only has 3 slices
		para_1 = ''
		para_2 = ''
		para_3 = ''
		# 1
		'''
		1. 	i=0 --> mov cx,0
		i=X --> mov cx,X
		'''
		para_1 = params_list[0].replace('i=','')
		initiating = '''
	push cx
	mov cx,%s
LOOP_START_%s:
''' % (get_counter(),para_1)

		# 2
		'''
		2. 	i<=N --> cmp cx,N; jle LOOP_START
		i<N --> cmp cx,N; jl LOOP_START
		i>=N --> cmp cx,N; jge LOOP_START
		i>N --> cmp cx,N; jg LOOP_START
		i!=N --> cmp cx,N; jne LOOP_START
		'''
		
		if '<=' in params_list[1]:
			foobar = params_list[1].replace('i','').replace('<=','')
			bound = """
cmp cx,%s
jle LOOP_START_%s
			""" % (foobar,get_counter())
		elif '>=' in params_list[1]:
			foobar = params_list[1].replace('i','').replace('>=','')
			bound = """
cmp cx,%s
jge LOOP_START_%s
			""" % (foobar,get_counter())
		elif '<' in params_list[1]:
			foobar = params_list[1].replace('i','').replace('<','')
			bound = """
cmp cx,%s
jl LOOP_START_%s
			""" % (foobar,get_counter())
		elif '>' in params_list[1]:
			foobar = params_list[1].replace('i','').replace('>','')
			bound = """
cmp cx,%s
jg LOOP_START_%s
			""" % (foobar,get_counter())
		elif '!' in params_list[1]:
			foobar = params_list[1].replace('i','').replace('!','')
			bound = """
cmp cx,%s
jne LOOP_START_%s
			""" % (foobar,get_counter())



		'''
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
		if '++' in params_list[2]:
			iteration = 'inc cx'
		elif '--' in params_list[2]:
			iteration = 'dec cx'
		elif '+=' in params_list[2]:
			foobar = params_list[2].replace('i+=','')
			iteration = '''add cx,%s''' % foobar
		elif '-=' in params_list[2]:
			foobar = params_list[2].replace('i-=','')
			iteration = '''dec cx,%s''' % foobar
		elif '*=' in params_list[2]:
			foobar = params_list[2].replace('i*=','')
			iteration = '''
	push ax
	push dx
	mov ax,cx
	mov dl,%s
	mul dl
	mov cx,ax
	pop dx
	pop ax
			''' % foobar
		elif '/=' in params_list[2]:
			foobar = params_list[2].replace('i/=','')
			iteration = '''
	push ax
	push dx
	mov ax,cx
	mov dl,%s
	div dl
	xor ah,ah
	mov cx,ax
	pop dx
	pop ax
			''' % foobar
		elif '%=' in params_list[2]:
			foobar = params_list[2].replace('i%=','')
			iteration = '''
	push ax
	push dx
	mov ax,cx
	mov dl,%s
	div dl
	mov al,ah
	xor ah,ah
	mov cx,ax
	pop dx
	pop ax
''' % foobar
		elif '<<=' in params_list[2]:
			foobar = params_list[2].replace('i<<=','')
			iteration = '''shl cx,%s''' % foobar
		elif '>>=' in params_list[2]:
			foobar = params_list[2].replace('i>>=','')
			iteration = '''shr cx,%s''' % foobar
	

	#gen. codes
	add_code(initiating)

	bar = lexer.get_token() # remove {
	if bar != '{':
		print 'ERROR'
		sys.exit(0)
	else:
		# context
		while True:
			ret = key_statement(lex)
			if ret != None and ret != '':
				break
			pass
		add_code(iteration)
		
		add_code(bound)
	counter()

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
;assign
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
		codes = Template(pattern).substitute({'REG':reg_type,'SOURCE':lexer_resource[source][1]})

		add_code(codes)
	def _plus():
		# Binary
		immediate_num = True
		another = lexer.get_token()

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
;add two number
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
			codes = Template(pattern).substitute({'REG':reg_type,'FIRST':lexer_resource[source][1],'SECOND':lexer_resource[another][1]})
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


	# ******************************

	opt_method = {'=':_assign,
				  '+':_plus}
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