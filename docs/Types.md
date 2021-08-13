# Types

**void**
```rust
void x;
```

**Integer Types**
```rust
//types
byte: i8
short: i16
int: i32
long: i64
//usage 1
int x = 69420;
//usuage 2
i32 x = 42069;
```

**Floating Point Types**
```rust
//types
half: 16 bit
float: 32 bit
double: 64 bit
huge: 128 bit
//usage 1
double x = 420.69;
//usage 2
f64 x = 420.69;
```

**Text Types**
```rust
//types
char: ui8
string: ui8[n]
//usage 1
char x = 'd';
string y = "hi";
//usage 2
ui8 x = 'd';
ui8[8] y = "hi"
```


**Boolean Type*
```rust
//usuage
bool x = false;
```

**Arrays**
```rust
//usage
int[6] x = 2; //every element will have 2 as the default value
int[3] x = {3,7,2};
println("%i".format(x[0])); //accessing members
```

**Structs**
```rust
//creation
struct Rectangle {
    int x;
    int y;
    int width;
    int height;
}
//usage
Rectangle myrect = {0,0,10,10};
//accessing members
myrect.x;
myrect["width"];
```