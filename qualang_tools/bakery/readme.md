# Waveform baking
This library introduces a new framework for creating arbitrary waveforms and storing them in the usual configuration file. 
The idea is to simplify the writing of pulse samples without the limitation imposed by the hardware. Using this tool provides an advantage by embedding into one single waveform a series of instructions that allows program memory preservation.
Waveform baking is done via a new context manager, declared prior to the QUA program, that takes two inputs: 

- the configuration dictionary (the same used to initialize a Quantum Machine instance),

- a padding method: to be chosen between: “right”, “left”, “symmetric_l”, “symmetric_r”. This string indicates how samples should be filled up with 0s when they do not match hardware constraints (that is if waveform's length is not a multiple of 4 or is shorter than 16 ns). 

    -  “right” setting is the default setting and pads 0s at the end of the baked samples

    - “left” pads 0s before the baked samples

    - “symmetric_l” pads 0s symmetrically before and after the baked samples, putting one more 0 before it in case the baked waveform's length is odd

    - “symmetric_r' pads 0s symmetrically before and after the baked samples , putting one more 0 after it in case the baked waveform's length is odd
- update_config: boolean indicating if the baked waveform shall be inserted in the input configuration (default value set to True)
- override: boolean indicating if the baked waveform shall bear the flag "is_overridable" in the config (see example below with add_compiled, default value set to False)

The simplest declaration is done before the QUA program as follows: 

```
with baking(config, padding_method = "symmetric_r") as b:
  b.align("qe1", "qe2", "qe3")
  b.frame_rotation(0.78, "qe2")
  b.ramp(amp=0.3, duration=9, qe="qe1")
```

When executed, the content manager edits the input configuration file and adds:
- an operation for each quantum element involved within the baking context manager
- an associated pulse
- an associated waveform (set of 2 waveforms for a mixedInputs quantum element) containing waveform(s) issued from concatenation of operations indicated in the context manager.


# **How can I add operations inside the baking context manager?**

The logic behind the baking context manager is to stay as close as possible to the way we would write play statements within a QUA program. For instance, commands like frame_rotation, reset_phase, ramp, wait and align are all replicated within the context manager. 

The procedure for using baked operations is as follows:

1. You first have to write down the samples you want to use as a waveform in the form of a Python list.
    - If the samples is meant for a singleInput element, the list should contain the samples itself. 
    - Contrariwise, if it is intended for a mixInputs element, the list should contain two Python lists as ```[sample_I, sample_Q]``` , where sample_I and sample_Q are themselves Python lists containing the samples.

2. Add the samples to the local configuration, with method ```add_Op```, which takes 4 inputs: 
    - The name of the operation (name you will use only within the baking context manager in a play statement)
    - The quantum element for which you want to add the operation
    - The samples to store as waveforms
    - The digital_marker name (supposedly already existing in the configuration) to attach to the pulse associated to the operation.

3. Use a baking ``play()`` statement, specifying the operation name (which should correspond to the name introduced in the add_Op method) and the quantum element to play the operation on

All those commands concatenated altogether eventually build one single “big” waveform per quantum element involved in the baking that contains all the instructions specified in the baking environment. The exiting procedure of the baking ensures that the appropriate padding is done to ensure that the OPX will be able to play this arbitrary waveform.

Here is a basic code example that simply plays two pulses of short lengths: 


```
with baking(config, padding_method = "symmetric_r") as b:

# Create arbitrary waveforms 

  singleInput_sample = [1., 0.8, 0.6, 0.8, 0.9]
  mixInput_sample_I = [1.2, 0.3, 0.5]
  mixInput_sample_Q = [0.8, 0.2, 0.4]
  
  # Assign waveforms to quantum element operation
  
  b.add_Op("single_Input_Op", "qe1", singleInput_sample, digital_marker= None)
  b.add_Op("mix_Input_Op", "qe2", [mixInput_sample_I, mixInput_sample_Q], digital_marker = None)
  
  # Play the operations
  
  b.play("single_Input_Op", "qe1")
  b.play("mix_Input_Op", "qe2")
```
# **How to play in QUA my baked waveforms?**

The baking object has a method called run, which takes no inputs and simply does appropriate alignment between quantum elements involved in the baking and play simultaneously (using this time a QUA play statement) the previously baked waveforms. Therefore, all that is left is to **call the run method associated to the baking object within the actual QUA program**.

```
with baking(config, "left"):
  #Create your baked waveform, see snippet above
  
#Open QUA program: 
with program() as QUA_prog:
  b.run()
```

As in QUA, you can still modulate in real time (using QUA variables) properties of the pulse like its amplitude, or to truncate it.
You can indeed pass into a set of two lists, parameters for truncating pulses and for amplitude modulation. The syntax goes as follows:
```
with program() as QUA_prog:
    truncate = declare(int, value = 18)
    amp = declare(fixed, value = 0.4)
    b.run(amp_array = [(qe1, amp), (qe2, 0.5)], truncate_array = [(qe1, truncate), (qe3, 74)]) 
```
Note that you do not have to provide tuples for every quantum element. The parameters you can pass can either Python or QUA variables. Beware though, you should make sure that the elements
indicated in the parameter arrays are actually used within the baking context manager.
# **Additional features of the baking environment**

The baking aims to be as versatile as possible in the way of editing samples. The idea is therefore to generate desired samples up to the precision of the nanosecond, without having to worry about its format and its insertion in the configuration file. It is even possible to generate a waveform based on two previous samples (like a pulse superposition) by using two commands introduced in the baking: ``play_at()`` and ``negative_wait()``.

Let’s take a look at the code below to understand what these two features do: 

```
with baking(config=config, padding_method="symmetric_r") as b:
    const_Op = [0.3, 0.3, 0.3, 0.3, 0.3]
    const_Op2 = [0.2, 0.2, 0.2, 0.3, 0.4]
    b.add_Op("Op1", "qe1", [const_Op, const_Op2]) # qe1 is a mixInputs element
    Op3 = [1., 1., 1.]
    Op4 = [2., 2., 2.]
    b.add_Op("Op2", "qe1", [Op3, Op4])
    b.play("Op1", "qe1")   
    
    # The baked waveform is at this point I: [0.3, 0.3, 0.3, 0.3, 0.3]
    #                                     Q: [0.2, 0.2, 0.2, 0.3, 0.4]
    
    b.play_at("Op3", "qe1", t=2)
    # t indicates the time index where these new samples should be added
    # The baked waveform is now I: [0.3, 0.3, 1.3, 1.3, 1.3]
    #                           Q: [0.2, 0.2, 2.2, 2.3, 2.4]
    
At the baking exit, the config will have an updated samples 
adapted for QUA compilation, according to the padding_method chosen, in this case:
I: [0, 0, 0, 0, 0, 0.3, 0.3, 1.3, 1.3, 1.3, 0, 0, 0, 0, 0, 0], 
Q: [0, 0, 0, 0, 0, 0.2, 0.2, 2.2, 2.3, 2.4, 0, 0, 0, 0, 0, 0]
```
If the time index t is positive, the samples will be added precisely at the index indicated in the existing samples.
Contrariwise, if the provided index t is negative, we call here automatically the function ``negative_wait()``, which adds the samples at the provided index starting to count from the end of the existing samples: 
```
with baking(config=config, padding_method="symmetric_r") as b:
    const_Op = [0.3, 0.3, 0.3, 0.3, 0.3]
    const_Op2 = [0.2, 0.2, 0.2, 0.3, 0.4]
    b.add_Op("Op1", "qe1", [const_Op, const_Op2]) #qe1 is a mixInputs element
    Op3 = [1., 1., 1.]
    Op4 = [2., 2., 2.]
    b.add_Op("Op2", "qe1", [Op3, Op4])
    b.play("Op1", "qe1")   
    # The baked waveform is at this point I: [0.3, 0.3, 0.3, 0.3, 0.3]
    #                                     Q: [0.2, 0.2, 0.2, 0.3, 0.4]
    b.play_at("Op3", "qe1", t=-2) #t indicates the time index where these new samples should be added
    # The baked waveform is now I: [0.3, 0.3, 0.3, 1.3, 1.3, 1.0]
    #                           Q: [0.2, 0.2, 0.2, 2.3, 2.4, 2.0]
    
At the baking exit, the config will have updated samples 
adapted for QUA compilation, according to the padding_method chosen, in this case: """
I: [0, 0, 0, 0, 0, 0.3, 0.3, 0.3, 1.3, 1.3, 1.0, 0, 0, 0, 0, 0], 
Q:  [0, 0, 0, 0, 0, 0.2, 0.2, 0.2, 2.3, 2.4, 2.0, 0, 0, 0, 0, 0]
```
The ``play_at()`` command can also be used as a single play statement involving a wait time and a play statement. In fact, if the time index indicated in the function is actually out of the range of the existing samples, a wait command is automatically added until reaching this time index (recall that the index corresponds to the time in ns) and starts inserting the operation indicated at this time. See the example below: 

```
with baking(config=config, padding_method="symmetric_r") as b:
    const_Op = [0.3, 0.3, 0.3, 0.3, 0.3]
    const_Op2 = [0.2, 0.2, 0.2, 0.3, 0.4]
    b.add_Op("Op1", "qe1", [const_Op, const_Op2]) #qe1 is a mixInputs element
    Op3 = [1., 1., 1.]
    Op4 = [2., 2., 2.]
    b.add_Op("Op2", "qe1", [Op3, Op4])
    b.play("Op1", "qe1")  
    # The baked waveform is at this point I: [0.3, 0.3, 0.3, 0.3, 0.3]
    #                                     Q: [0.2, 0.2, 0.2, 0.3, 0.4]
    b.play_at("Op3", "qe1", t=8) #t indicates the time index where these new samples should be added
    # The baked waveform is now 
    # I: [0.3, 0.3, 0.3, 0.3, 0.3, 0, 0, 0, 1.0, 1.0, 1.0], 
    # Q: [0.2, 0.2, 0.2, 0.3, 0.4, 0, 0, 0, 2.0, 2.0, 2.0]}
    #                                    
    
At the baking exit, the config will have updated samples 
adapted for QUA compilation, according to the padding_method chosen, in this case:
I: [0.3, 0.3, 0.3, 0.3, 0.3, 0, 0, 0, 1.0, 1.0, 1.0, 0, 0, 0, 0, 0], 
Q: [0.2, 0.2, 0.2, 0.3, 0.4, 0, 0, 0, 2.0, 2.0, 2.0, 0, 0, 0, 0, 0]
```

# The negative wait

Negative wait is at the moment, just an equivalent way of writing the ``play_at()`` statement.

The idea is to move backwards the time index at which the following play statement should start (wait[-3] means that the following waveform will be added on top of the existing sequence on the 3 last samples and will append the rest like a usual play statement.

We have the equivalence between:
```
b.wait(-3)
b.play('my_pulse',qe)
```
and 
```
b.play_at('my_pulse', qe, t=-3)
```

# Retrieving the baked waveforms

The baking tool can also be used as a simple waveform generator, without having to necessarily update the configuration 
file with associated new operations and pulses. A good use case is the precompile feature and the
overridability of waveforms in order to save waveform memory (see example below).
To do so, one can simply do the following :

```
with baking(config, padding_method = "right",
            update_config = False) as b :
    # Generate the desired set of baked waveforms
     # (one per involved quantum element)
    
waveforms_dict = b.get_waveforms_dict()
```
# **Examples**

## Ramsey at short time scales
[Ramsey](Ramsey_Gauss_baking.py) - In this baking example, we are creating pulses for a Ramsey experiment in which the 
$$\pi/2$$ pulses are made using gaussian with a width of 5 ns, and the distance between the two pulses changes from 0 to 
32 ns. It is also possible to change the phase of the second pulse using the *dephasingStep* parameter. The resulting
pulses are plotted, it is important to remember that these pulses are in the baseband, and will be multiplied by the IF
matrix (and later mixed with an LO).

### Generating short Ramsey pulse sequences with waveform baking

This tutorial presents a use case for the waveform baking tool, which facilitates the
generation of pulse samples that are shorter than 16 ns, which would usually have to be manually
modified to upload it to the OPX.

Using the baking environment before launching the QUA program allows the pulse to be seamlessly 
integrated in the configuration file, without having to account for the restrictions of pulse length 
imposed by QUA.

It also provides a simpler interface to generate one single waveform that can contain several
play statements (preserving program memory).

The experiment is as follows:

We have a superconducting qubit (controlled using the quantum element 'Drive' in the configuration
file) coupled to a readout resonator ('Resonator') with which we would like to apply sequences
of two short Gaussian pulses spaced with a varying time duration, followed directly by a probe 
coming from the resonator (the measurement procedure should start immediately after the second Gaussian 
pulse was played by the Drive element).

The baking environment is used here to synthesize without any effort a waveform resulting from delayed
superposition of two Gaussian pulses (a simple *play* followed by a *play_at* with a varying delay).
Note that we also use an initial delay to ensure that there is a perfect
synchronization between the end of the Ramsey sequence, and the trigger of the resonator
for probing the qubit state.

Within the QUA program, what remains to do is simply launching the created baking objects within
a Python for loop (using the *run* command) and use all appropriate commands related to the resonator to build your experiment. 



# Randomized benchmarking for 1 qubit with waveform baking

Waveform baking is a tool to be used prior to running a QUA program to store waveforms and play them 
easily within the QUA program without having to require a series of play statements.

It turns out that this economy of statements can be particularly useful for saving program 
memory when running long characterization experiments that do require lots of pulses to be played,
such as tomography experiments (usually involving state preparation, process, and readout for each couple of input state 
and readout observable to be sampled) or randomized benchmarking.
Randomized benchmarking principles are reminded in another example done in QUA: https://docs.qualang.io/libs/examples/randomized-benchmark/one-qubit-rb/
Here, the idea is to show the ease with which we can integrate tools associated to waveform baking to the example realized in the existing QUA script ,
by taking the same elementary built-in functions to generate the entire quantum circuit necessary to run the random sequence. 
With the use of the baking, we now have one single baked waveform randomly 
synthesized.

# Coupling the baking tool to the add_compile feature

QUA allows you to pre_compile a job in order to save compilation time. This aspect is reminded in this part of 
the documentation (https://qm-docs.s3.amazonaws.com/v1.10/python/features.html#precompile-jobs).
It is possible to easily override waveforms by doing two things :
1. Create a baking object ```b_ref ```setting both ```update_config ``` and ```override ``` parameters to True. Note that
this will attach to each waveform created for all quantum elements involved in the context manager the flag ```is_overridable ``` 
to True in the input config 
2. Since the new waveform that shall be overriding the waveform created in 1 should be of same length, 
the newly baked object ```b_new ``` shall contain the information about the reference length it should target. This is done 
by specifying a new parameter ```baking_index ``` that shall be set to the baking index of ```b_ref ``` using the method
```b_ref.get_baking_index() ```
3. One can finally specify the ```overrides ``` argument of the ```qm.queue.add_compiled ``` with the dictionary
```b_new.get_waveforms_dict() ```



