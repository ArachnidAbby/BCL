Methods
========

Methods are functions on structs. These have special properties that are slightly different than functions.
The main one being automatic referencing.


########################
Defining a basic method
########################

.. code-block:: bcl

    import stdlib::*;

    struct MyStructure {
        x: i32,
        y: i32;

        // defining a struct FUNCTION

        // "Self" is a special type that exists inside of structs.
        // In this case, it refers to "MyStructure"
        define new(x: i32, y: i32) -> Self {
            return Self {
                x: x,
                y: y
            };
        }

        // defining a struct METHOD

        // self is just the first argument, when we don't define a type,
        // it is assumed we want a method. "self" can be named anything you want
        // "self" is just common convention. Sometimes this argument is called "this",
        // in other languages
        define get_x(self) -> i32 {
            return self.x;
        }
    }

    define main() {
        my_instance = MyStructure::new(10, 20); // use a struct function
        //                       ^^
        //    accessed with the namespace operator

        println(my_instance.get_x()); // use the struct method
        //                 ^
        // accessed with the member access operator
    }

####################################################
Trying to access struct methods without an instance
####################################################

You **cannot** do this. The language only lets you access these methods when you have
an instance to use them with. That is another thing that makes them different than methods.

################
Mutable Methods
################

Mutable methods let you modify the instance that you are working with.
These are very helpful.

.. code-block:: bcl

    import stdlib::*;

    struct MyStructure {
        x: i32,
        y: i32;

        // defining a struct FUNCTION

        // "Self" is a special type that exists inside of structs.
        // In this case, it refers to "MyStructure"
        define new(x: i32, y: i32) -> Self {
            return Self {
                x: x,
                y: y
            };
        }

        // defining a struct METHOD

        // "&self" is used to define a mutable method. Names other than "self"
        // can be used here too!
        define set_x(&self, value: i32) {
            self.x = value; // has side-effects
        }
    }

    define main() {
        my_instance = MyStructure::new(10, 20); // use a struct function
        //                       ^^
        //    accessed with the namespace operator

        my_instance.set_x(22); // call mutable method

        println(my_instance.x);
    }


################
Method Chaining
################

Method chaining is where you have mutable methods that return
a reference to the instance.

This is useful if you have a "builder pattern".

.. code-block:: bcl

    import stdlib::*;

    struct Student {
        grade_level: i8, // could be wise to use an enum!
        classes: i8, // number of classes
        GPA: f32;

        define new() -> Self {
            return Self {
                grade_level: 0,
                classes: 0,
                GPA: 4.0
            };
        }

        define set_classes(&self, count: i8) -> &Self {
            self.classes = count;
            return self;
        }

        define set_GPA(&self, new_gpa: f32) -> &Self {
            self.GPA = new_gpa;
            return self;
        }

        define set_grade_level(&self, new_level: i8) -> &Self {
            self.grade_level = new_level;
            return self;
        }
    }

    define main() {
        my_student = Student::new();

        // use method chaining
        my_student.set_classes(8)
                  .set_GPA(3.2)
                  .set_grade_level(11);

        // alternatively, we could do this:
        my_student = *(Student::new() // dereference with `*`
                        .set_classes(8)
                        .set_GPA(3.2)
                        .set_grade_level(11));
    }