# What are functions

functions are essentially just blocks of code that can be condensed into one method call.

**example**
```cpp
myfunc(...args);
```

# How do I write function in BCL

```rust
func myFunction() { // basic void function without any arguements
	println("Hello World");
}

func printText(string text) { // void function that takes in arguements.
	println(text);
}

func addNumbers(int x, int y) -> int { // basic function with args that returns an int
	return x+y;
}

myFunction();
printText("It works!");
println(addNumbers(2,2));
```

```
Hello World
It works!
4
```