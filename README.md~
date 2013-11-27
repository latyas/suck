suck
====

实验课老师都是蛋疼无比的，不过，魔高一尺，道高一丈，对付实验课老师自有办法！
抱歉有很多调试输出的东西没有删掉。

等待实现的功能,预计一天写一个

going to do:
	11-28 把花括号匹配重写，实现函数定义和调用
1.函数定义

返回类型 function_name(参数列表){
}
(目前考虑重写key_statement 把{}的匹配计算进去才识别的出代码块的起始
不考虑closure的实现)

2.函数调用

function(参数列表);

3.while语句
while(真值)
{
	body
}
4.break和continue语句实现

5.对指针显式解引用

6.if语句 (if/elif/else)
(考虑遇到if先生成花括号内代码，遇到下一个花括号检测else和elif
遇到if时压入if_stack中一个标记
1. 如果遇到的是elif，则压入一个相同的标记（此时有两个标记）
2.遇到else则将标记输出到else起始位置
3.遇到没有else的右花括号则将if_stack中所有栈顶标记全部清除

形成类似如下的代码
if  -> if_stack.push(IF_some counter)

[elif -> if_stack.push(if_stack[-1])]

[else
	if_stack.pop
	if_stack.remove(IF_the counter)
	]

7.结构体

tips:
	现在还没有测试对表达式的计算，这个看需要似乎要重写。
	需要写一些C的基本的函数

important:
	这玩意代码很垃圾，纯粹为了考试方便
	代码要求写的标准，实现基本的伪C就行了
	数据类型虽然内置了BYTE WORD DWORD，不过只需要BYTE和WORD即可，BYTE用于基本的存储操作，WORD是为了方便一些简单的整数计算/迭代器和指针用（short类型）
Example:

	main()
	{
		WORD k;
		WORD i;
		WORD sex[100];
	
		sex[5] = 1;
		
		for(k=0;k<10;k++)
		{
			puts("Hello, SHIYANKELAOSHI.");
		}
	}


output:

	data segment
		_heap dw 32768 dup (0)
		_hp dw 0
		_buffer dw 4096 dup (0)
		_user_stack dw 4096 dup (0)
		_user_stack_ptr dw 0
		STRING_7 db "Hello, SHIYANKELAOSHI.",13,10,"","$"
		
	ends
	stack segment
		
		dw 128 dup (0)
		
	ends
	code segment
	
	start:
		; set segment registers:
		mov ax, data
		mov ds, ax
		mov es, ax
	
		;initiate _hp , _user_stack_ptr
		mov _hp,offset _heap
		mov _user_stack_ptr,offset _user_stack
		
	
		;push to user stack
		push bx
		mov bx,[_user_stack_ptr]
		mov [bx],1
		add _user_stack_ptr,2
		pop bx
		;push END
				
		
		;pop to dest
		push ax
		push bx
		mov bx,[_user_stack_ptr]
		mov ax,[bx-2]
		mov dx,ax
		sub _user_stack_ptr,2
		pop bx
		pop ax
		;pop END
				
		
		;assign [_heap+9],sex
		mov [_heap+9],dx
		;end assign
				
		
		;push to user stack
		push bx
		mov bx,[_user_stack_ptr]
		mov [bx],0
		add _user_stack_ptr,2
		pop bx
		;push END
				
		
		;pop to dest
		push ax
		push bx
		mov bx,[_user_stack_ptr]
		mov ax,[bx-2]
		mov dx,ax
		sub _user_stack_ptr,2
		pop bx
		pop ax
		;pop END
				
		
		;assign k
		mov [_heap+0],dx
		;end assign
				
		LOOP_FOR_3:
		
		push dx
		lea dx,STRING_7
		mov ah,9
		int 21h
		pop dx
			
		inc [_heap+0]
		
		;_less ax < 10
		push ax
		mov ax,[_heap+0]
		cmp ax,10
		jl LOOP_FOR_3:
		pop ax
		;less cmp end
				
		LOOP_FOR_3_END:
		
	
		; wait for any key....    
		mov ah, 1
		int 21h
	
		mov ax, 4c00h ; exit to operating system.
		int 21h
	      
		
		
	ends
	
	end start
