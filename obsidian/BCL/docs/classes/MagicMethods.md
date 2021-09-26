# What are magic methods?

Magic methods are called when doing basic things such as printing a class or adding two of the same class together.

# List of all magic methods

-  `~add(type other)->type`
-  `~sub(type other)->type`
-  `~mul(type other)->type`
-  `~div(type other)->type`
-  `~addself(type other)`
-  `~subself(type other)`
-  `~mulself(type other)`
-  `~divself(type other)`
-  `~index(type x)->type`
-  `~cast(type x)->type`
-  `~repr()->string||char[]`
-  `~del()->void`

# Examples

## Math!

```rust
testClass x = testClass(2); //testClass is just a wrapper for an integer :)

x+=28; //calls x.~addself(...) -> this
println(x); // calls x.~repr()
```

```
30
```

## indexing!

```rust
testClass x = testClass(2, 9); //testClass is just a wrapper for an integer array. 2 is the default value, 9 is the array length.

int y =x[7]; //calls x.~index(7) -> int
println(y); 
```

```
2
```


## example class!

```cpp
class testClass { //another integer wrapper
	int value; //our instance variable
	
	testClass(int value){ //constructor
		this.value = value;
	}
	
	func ~add(int other) -> testClass{ // this+8
		return testClass(value+other);
	}
	
	func ~sub(int other) -> testClass{ // this-8
		return testClass(value-other);
	}
	
	func ~addself(int other) { // this+=8
		value+=other
	}
	
	func ~subself(int other) { // this-=8
		value-=other
	}
}
```