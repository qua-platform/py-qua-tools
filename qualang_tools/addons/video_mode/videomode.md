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
    
    with infinite_loop():
        video_mode.load_parameters()
        
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


The ```VideoMode```, once launched in Python, will query continuously the user to input (through the keyboard) 
the name of parameter, and the associated new value it should take.
The format should be written as follows:
```
param_name=new_value
```
The user can also update a parameter that is a QUA array by providing a list of values separated by a space:
```
param_name= new_value_1 new_value_2 new_value_3 ...
```

Once the user has typed an appropriate update, the ```VideoMode``` will use the IO variables of the ``QuantumMachine`` 
to pass the following information:
- which parameter of the initial dictionary should be updated next (IO1)
- what new value should be set for the parameter (IO2)

For updating a QUA array, a loop over the elements of the array is performed to update dynamically each element 
with a successive back and forth interaction between the program and the Python (through interleaved ```pause()``` within QUA and ```job.resume()``` in Python).

The only thing that the user should implement in the QUA program on top of the declaration of variables shown above is the following macro:
```
with program() as video_mode_prog:
    ...
    with infinite_loop():
        video_mode.load_parameters()
        ...
```

### Accessing QUA variables from ```VideoMode``` within the program
The QUA variables declared in the program through the ```VideoMode.declare_variables()``` can be accessed from the
through the ```video_mode["param_name"]``` syntax. This enables you to choose where your QUA variable should land in 
your program. For instance, if you want to use the same QUA variable for two different pulse parameters, you can do the following:
```
with program() as video_mode_prog:
    video_mode.declare_variables()
    
    with infinite_loop():
        video_mode.load_parameters()
        
        play("my_pulse"*amp(video_mode["amp_param"]), "qe1")
        play("my_other_pulse"*amp(video_mode["amp_param"]), "qe2")
```

## Outside the QUA program
The ```VideoMode``` class has only one ```execute```method to be called outside the QUA program scope, which takes the same arguments as the 
```qm.execute()``` method. It will start the video mode execution by starting a new thread launching the QUA program and a continuous query of input parameters from the user.
Note that the QUA program runs in the background and the user can still interact with the Python environment while the program is running.


To start the VideoMode, The user just has to call the ```start()``` method of the ```VideoMode``` object. The user can choose to call it
either before or after the QUA program execution. If before, the user should provide the QUA program and the VideoMode object will automatically execute the program while launching a new thread.


  