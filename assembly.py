from string import Template
IN_CONDITION_SINGLE = '''
	mov ax,$OP1
	$OPT ax,$OP2
	jne $PREFIX-L1
	$STATEMENTS
$PREFIX-L1:
'''


data = {'OPT':'cmp','OP1':'[bx]','OP2':'[bx+2]','PREFIX':'PROG1','STATEMENTS':'''
	hahahaha
	hohohoo'''}

print Template(IN_CONDITION_SINGLE).substitute(data)