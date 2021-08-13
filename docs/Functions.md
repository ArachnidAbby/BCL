# Functions

functions use the `func` keyword! Below you will see an example. ⬇


*code*
```java
///////////////////
// Functions.bcl //
///////////////////

func is_even(int x) : boolean {//returns a boolean!
    return (x%2)==0;
}

int user_input = input("enter a number ").as_int();
if is_even(user_input)
    println("Your number was even!");
else
    println("Your number was odd!");
```

*output*
<pre>
<span style="color:red;">~$</span><span style="color:blue"> BCL -compileSingle -autoExecute Functions.bcl</span>
<span style="color:green;">enter a number </span><span style="color:grey">69</span>
<span style="color:green;">Your number was odd!</span>
</pre>