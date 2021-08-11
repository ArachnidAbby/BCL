	.text
	.file	"test.ll"
	.globl	main                    # -- Begin function main
	.p2align	4, 0x90
	.type	main,@function
main:                                   # @main
# %bb.0:                                # %entry
	pushq	%rax
	movl	$.str, %edi
	xorl	%eax, %eax
	callq	printf
	xorl	%eax, %eax
	popq	%rcx
	retq
.Lfunc_end0:
	.size	main, .Lfunc_end0-main
                                        # -- End function
	.type	.str,@object            # @.str
	.section	.rodata,"a",@progbits
.str:
	.asciz	"hello, world\n"
	.size	.str, 14

	.section	".note.GNU-stack","",@progbits
