# Video Mode
## Introduction

In some cases, one might want to update parameters of the program while it is running and without knowing in advance when and how to update them.
We present here the ```VideoMode``` which enables such dynamic parameter tuning.

## How to use it

The user can declare a ``VideoMode`` instance by passing in a ```QuantumMachine``` instance and a dictionary of
parameters intended to be updated dynamically. Additionally, if a job is already started on the ```QuantumMachine```,
it can also use this job to change dynamically some of its parameters (this assumes that the QUA program associated to this job
was already designed to be compatible with the ```VideoMode```, which we will explain how to do below).


The dictionary must be of the form:

```
parameters_dict = {
    'parameter_name_1': parameter_value_1,
    'parameter_name_2': parameter_value_2,
    ...
}
```
The values of the dictionary can be Python variables for which a QUA variable can be declared. The possible types are:
- ```bool```, ```ìnt``` ,```float```(the latter would be cast to QUA ```fixed```)
- ```list``` or 1D ```ndarray``` (to be cast to QUA ```array```)

The simplest declaration of the VideoMode can be done as:
```
qmm = QuantumMachinesManager()
qm = qmm.open_qm(config)
video_mode = VideoMode(qm, parameters_dict)
 ```

Once this declaration is done, some interesting thing will happen behind the scenes.

First, the provided dictionary of parameters will be converted to a ```ParameterTable``` instance.
The ```ParameterTable``` class serves as an interface between the QUA program and the Python environment. 
It is used to facilitate the declaration of the QUA variables that are suitable for the parameters to be updated.
It contains two methods that should be used as QUA macros to enable the dynamic parameter update:
  - ```declare_variables```: declares all the necessary QUA variables based on the parameters signature of the ```ParameterTable```object. 
        This method should ideally be called at the beginning of the QUA program scope.
  - ```load_parameters```: handles the dynamic assignment of the parameters declared in the QUA program scope through the IO variables.

For convenience, those macros can be accessed directly through the ```VideoMode``` object. The QUA program should therefore 
start look like this:

```
with program() as video_mode_prog:
    video_mode.declare_variables()
    param_indexing_var = declare(int)
    loop_var = declare(int)
    
    with infinite_loop():
        video_mode.load_parameters(param_indexing_var, loop_var)
        
        play("my_pulse"*amp(video_mode["amp_param"]), "qe1")
        
       
```

Let us explain what we did here.

### Declaring variables
The first line within the program is essentially a macro that has declared all the QUA variables dynamically from the 
original parameter list by operating an appropriate casting for all parameters that were provided by the user.

To be able to access those newly created QUA variables later in the design of the program, we can use 
```video_mode["param_name"]``` for each parameter loaded initially in the dictionary. We can then use those variables 
as we please within the program, as shown above with the custom amplitude parameter ```"amp_param"```.

### Updating variables dynamically

As you can see in the code snippet above, we declared two QUA int variables that are then used in the method 
``load_parameters`` of the ```VideoMode```. To understand what they are here for, we should explain how the parameter update
is done dynamically behind the scene.
The ```VideoMode```, once launched in Python, will query continuously the user to input (through the keyboard) 
the name of parameter, and then its associated new value. 

Once the user has typed an appropriate update, the ```VideoMode``` will use the IO variables of the ``QuantumMachine`` 
to pass the following information:
- which parameter of the initial dictionary should be updated next (IO1)
- what new value should be set for the parameter (IO2)

To enable an easy mapping between the names of the parameters the user provide and an indicator in QUA of which parameter to update,
we use a simple indexing integer variable, ```param_indexing_var```, to perform the dynamic checking of which parameter to update next.

The second QUA int variable declared is called ```loop_var``` and is used within the macro ```load_parameters``` 
only when the parameter to be updated next is actually a QUA array. This variables loops over the elements of the array and dynamically updates each element of the array with a successive back and forth between the program and the Python (through interleaved ```pause()``` within QUA and ```job.resume()``` in Python).

## Outside the QUA program
The ```VideoMode``` class has 2 main methods to be called outside of the QUA program scope:
    - ```start()```: starts the video mode execution by starting a new thread calling the ``update_parameters()`` method
    - ``update_parameters()``: updates the parameters defined by the user with values provided by the user through Python ```input()``` function

To start the VideoMode, The user just has to call the ```start()``` method of the ```VideoMode``` object. The user can choose to call it
either before or after the QUA program execution. If before, the user should provide the QUA program and the VideoMode object will automatically execute the program while launching a new thread.


  