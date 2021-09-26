# What are enums?

Enums, or enumerators, or a way to pair a value with a keyword. In BCL they are modeled after Java Enums, which are just extensions on classes.

# Uses for enums.

Enums can be used in things like game Tilemaps for specifying tile names and values. They can also be used for naming tons of things like times of day, cordinal directions, days of the week, and more.


# Examples of basic enums

```java
enum tileSet{
	string name;
	int id;
	
	TileSet(string name, int id){ // constructor
		this.name = name;
		this.id = id
	}
	
	// VVV Enum Keywords VVV
	GRASS("grass", 0);
	DIRT("dirt", 1);
	STONE("stone", 2);
	// Note that keywords dont need to be capitalized.
}

enum cardinalDirection { // notice this has no constructor, these are just KEYWORDS.
	NORTH;
	SOUTH;
	EAST;
	WEST;
}


tileSet mytile = GRASS;
if(mytile == tileSet.GRASS)
	println("Its Grass Time");
```

```
Its Grass Time
```
