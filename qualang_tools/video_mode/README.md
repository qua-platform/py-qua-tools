# Video Mode
## Introduction

In some cases, one might want to update parameters of the program while it is running and without knowing in advance when and how to update them.
We present here the ```VideoMode``` which enables such dynamic parameter tuning.

## How to use it

The user can declare a ``VideoMode`` instance by passing in a ```QuantumMachine``` instance and a dictionary of
parameters intended to be updated dynamically.

The dictionary should be of the form:


```
parameters_dict = {
    'parameter_name_1': (parameter_value_1, qua_type_1),
    'parameter_name_2': (parameter_value_2, qua_type_2),
    ...
}
```
where ```qua_type``` can be ```bool```, ```ìnt``` or ```fixed```.
If a list of values is provided, the subsequent QUA variable will be a QUA array of specified type.


The simplest declaration of the VideoMode can be done as follows:
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

For convenience, those macros can be accessed directly through the ```VideoMode``` object. The QUA program should therefore look like this:

```
with program() as video_mode_prog:
    # Declare the QUA variables associated to the parameters
    video_mode.declare_variables()
    
    with infinite_loop():
        # Load the parameters from the Python environment
        video_mode.load_parameters()
        
        # Use the parameters as QUA variables
        play("my_pulse"*amp(video_mode["parameter_name_1"]), "qe1")
        frame_rotation(video_mode["parameter_name_2"], "qe1")
        
       
```

Let us explain what we did here.

### Declaring variables
The first line within the program is essentially a macro that has declared all the QUA variables dynamically from the 
original parameter list by operating an appropriate casting for all parameters that were provided by the user.

To be able to access those newly created QUA variables later in the design of the program, we can use 
```video_mode["param_name"]``` for each parameter loaded initially in the dictionary. We can then use those variables 
as we please within the program, as shown above with the custom parameters used for the QUA statements.

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

As everything happens behind the scenes, the user does not need to worry about the details of the implementation.
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

Note that you can also access to the full list of QUA variables declared in the program through the ```video_mode.variables``` attribute.

Alternatively, you can also access the QUA variables later in the code as follows 
(note that the order of the variables is the same as the order of the parameters in the `parameters_dict` as of Python 3.7):
```
with program() as video_mode_prog:
    amp_param1, amp_param2, ... = video_mode.declare_variables()
    
    with infinite_loop():
        video_mode.load_parameters()
        
        play("my_pulse"*amp(amp_param1), "qe1")
        play("my_other_pulse"*amp(amp_param2), "qe2")
```
## Outside the QUA program
The ```VideoMode``` class has only one ```execute```method to be called outside the QUA program scope, which is a simple wrapper of ```qm.execute()``` method.
It will start the video mode execution by creating a new thread that takes control of the console by doing a continuous query of input parameters from the user, while the QUA program is running in the background and possible live data plotting is done in the main script.
This new thread releases access of the console to the user once  ```stop``` is typed in the console.

## Example
Let us consider the following example where we want to update dynamically the amplitude and phase of a pulse.
We first declare the ```VideoMode``` instance and the parameters dictionary:
```
parameters_dict = {
    'amp': 0.5,
    'phase': 0.0
}
video_mode = VideoMode(qm, parameters_dict)
```
We then declare the QUA program as follows:
```
with program() as video_mode_prog:
    video_mode.declare_variables()
    
    with infinite_loop():
        video_mode.load_parameters()
        
        play("my_pulse"*amp(video_mode["amp"]), "qe1")
        frame_rotation(video_mode["phase"], "qe1")
```

Or an equivalent version:
```
with program() as video_mode_prog:
    amp_, phase = video_mode.declare_variables()
    
    with infinite_loop():
        video_mode.load_parameters()
        
        play("my_pulse"*amp(amp_), "qe1")
        frame_rotation(phase, "qe1")
```
Finally, we start the video mode execution:
```
video_mode.execute(video_mode_prog)
```
At this point, the python console accepts specific inputs, type `help` to see the full list. 
For example, to change the variables, type:

```
amp=0.8
phase=0.5
```
The program will then update the amplitude and phase of the pulse accordingly.

More detailed examples can be found under in [examples](https://github.com/qua-platform/py-qua-tools/tree/main/examples/Qcodes_drivers/video_mode) section.

  