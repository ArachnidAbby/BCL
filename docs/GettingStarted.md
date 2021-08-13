# Hello World Program

*code*
```java
////////////////////
// helloWorld.bcl //
////////////////////

println("Hello World");
```


*output*
<pre>
<span style="color:red;">~$</span><span style="color:blue"> BCL -compileSingle -autoExecute helloWorld.bcl</span>
<span style="color:green;">Hello World</span>
</pre>

*I know, how stunning*

In all seriousness I aim to keep this language easy to make simple scripts in while still allowing larger projects to be made with ease.


# "Whats your name" program.

*code*
```java
/////////////////////////
// questionProgram.bcl //
/////////////////////////


string userinput = input("What's your name? ");
println("Hello %s!".format(userinput));
```

*output*
<pre>
<span style="color:red;">~$</span><span style="color:blue"> BCL -compileSingle -autoExecute questionProgram.bcl</span>
<span style="color:green;">What's your name</span><span style="color:grey"> Benjamin</span>
<span style="color:green;">Hello Benjamin!</span>
</pre>

# Fizzbuzz program.

*code*
```java
//////////////////
// fizzbuzz.bcl //
//////////////////


int size = 100; 
for(int x; x<size;x++){
    if(x%3==0)
        print("fizz");
    else if(x%5==0)
        print("buzz");
    else
        print(x);
    println("");
}
```

*output*
<pre>
<span style="color:red;">~$</span><span style="color:blue"> BCL -compileSingle -autoExecute fizzbuzz.bcl</span>
<span style="color:green;">ITS FIZZBUZZ, WHAT DO YOU EXPECT? I'M NOT TYPING ALL THAT HERE!</span>
</pre>


