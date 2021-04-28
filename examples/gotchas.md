# Various Gotchas in running these examples

#### Importable modules

If you are using the `pipe_task -t <task>` option then `<task>` needs to be something
that lsst.utils.doImport can import.  In short if you have `<class>` in `<module>` then
`pipe_task -t <module>.<class>` should work.  Note that if you are trying out new code
that you haven't put in a package, you will need to set PYTHONPATH according, and that
your current directory might not be included in PYTHONPATH by default.


#### Overagressive configuration checking

The `pipe_task` framework is extremely agressive above configuration checking.  By
default it will not let you run different inputs into the same output collection,
nor will it let you run the same task with different configuration parameters or
connections, unless you change the label on the task.  If you are using a yaml file
to define a pipeline, the label is the key for the block where you define the task.
If you are running the task using the `pipe_task -t <task>` option, they you will
need to change the _DefaultName field in the task.  You will find when developing things
you end up with stuff like `_DefaultName = eoIsrCalibV12`  You will also probably have to
change the output connection name a few times and the output collection name a bunch of
times. (I got up to v21 developing these examples).


#### Finding calibrations

In most cases the `pipe_task` framework will try to identify a single instance of each
calibration input based on the timestamp of the exposure and validity ranges.  If this
is not the behavior you want, say because you know you want to use a single master bias
for all the images in a given run, they you will need to explicitly point pipe_task at
a RUN type collection with exactly one calibration that matches your input dimensions.

For example, in running `EoIsrExampleTask`, we have to point it at the RUN collections
that have the timestamps in the names, rather that the more human-readable CHAINED
collections.


#### Run on everything by default

By default, `pipe_task` will run on every data id in the input collections unless you specify
otherwise with the `-d` option.  If you are running on raw images it is _very_ easy to
mess up and forget to specify the run number and have `pipe_task` go off and decide to
run on a gazillion inputs.

To my mind, this is actually pretty dangerous default behavior.  It would be safer to have
leaving something out of a command result in nothing happening, as opposed to having it
result in a huge amount of stuff happening.  (Imagine if `rm` made you specifiy the files
you didn't want deleted instead of the files you did want deleted.)  However, I expect that
people have come to expect it by now, so we are probably stuck with it.  Try not to screw
this one up too many times.


#### Writing out lots of intermediate data products v. using sub-tasks

The way that tasks communicate is by writing intermediate data products to disk.
If you are doing something like trying a few different versions of the overscan and
bias subtraction and running a task to quantify the performance, and you use a
pipeline with IsrTask and your analysis Task, you will quickly find that you have
increased the size of the data on disk by 50x or more.

The way around this is to use sub-tasks to do the work.  The annoying bit is that
you have to handle the connections that the sub-tasks would normally handle and
call their `run()` methods yourself.






