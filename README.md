# leak_detector

In order to identify encoded, hashed or obfuscated leaks, we used **[Englehardt et al.’s method](https://petsymposium.org/2018/files/papers/issue1/paper42-2018-1-source.pdf)**. We adapt [Asuman] (https://github.com/leaky-forms/leaky-forms/tree/main/leak-detector) Leak Detector code to find leaks on post data, referer, and URLs. 

There are two Jupyter Notebook files that you can use `simple_checker` and `simple_analyzer`. `simple_checker` uses a JSON file as input and produces two csv files. You can use one of those csv files as input for the `simple_analyzer`.  