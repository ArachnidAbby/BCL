# What are Classes

Classes are a collection of functions, instance variables, and static variables. They can be useful in programming styles such as OOP. They have other uses of course, such as the string and list classes built in to the language.


# Basic Example

```cpp
 class vector2{
 	int x; // instance variables
	int y; // instance variables
	
 	vector2(int x, int y){ // constructor!
		this.x = x;
		this.y = y;
	}
	
	func length() -> int{
		return ((x**2)+(y**2))**0.5 //x and y reference the instance variables
	}
 }