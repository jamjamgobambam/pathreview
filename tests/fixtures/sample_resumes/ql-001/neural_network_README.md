<h1 align="center">neural-network</h1>

---
**neural-network** is a Python package on TestPyPi that provides a 
Multi-Layer Perceptron (MLP) framework built using only [**NumPy**](https://numpy.org/doc/stable/). 
The framework supports Gradient Descent, Momentum, RMSProp, and Adam optimizers.
<!-- TABLE OF CONTENTS -->
<details>
  <summary><h2>Table of Contents</h2></summary>
  <ol>
    <li><a href="#installation">Installation</a>
      <ul>
        <li><a href="#dependencies">Dependencies</a></li>
        <li><a href="#user-installation">User installation</a></li>
      </ul>
    </li>
    <li><a href="#simple-usage">Simple Usage</a>
      <ul>
        <li><a href="#designing-the-model-architecture">Designing the Model Architecture</a></li>
        <li><a href="#training-the-model">Training the Model</a></li>
        <li><a href="#making-predictions">Making predictions</a></li>
      </ul>
    </li>
    <li><a href="#beyond-the-framework">Beyond the Framework</a>
      <ul>
        <li><a href="#activation-functions">Activation functions</a></li>
        <li><a href="#loss-functions">Loss functions</a></li>
        <li><a href="#2d-decision-boundary">2D Decision Boundary</a></li>
      </ul>
    </li>
    <li><a href="#license">License</a></li>
  </ol>
</details>

## Installation

### Dependencies
```
python>=3.8
numpy>=1.22.1
matplotlib>=3.5.1 
```

### User installation
You can install neural-network using `pip`:
```
pip install neural-network
```

## Simple Usage

### Designing the Model Architecture
To define your MLP model, you need to specify the number of layers and the number of neurons in each one. \
Unless you want to manually set up the parameters, the size of the input layer is not needed, as it will be automatically determined in the initial training process.
```python
from neural_network import NeuralNetwork
model = NeuralNetwork(neurons=[64, 120, 1])
```
In this example, we have a four-layer neural network containing auto-defined input neurons, 
first hidden layer with 64 neurons, second hidden layer with 120 neurons, and one output neuron.

### Training the Model
To train the model, you need to provide the input data and the corresponding target (or label) data.
```python
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([[0], [1], [1], [0]])

model.fit(X, y, epochs=1000, learning_rate=0.1, optimizer='adam')
```
When training the model without setting the activation functions or/and the loss functions, the framework will automatically do the job for you. It will initialize the parameters and the functions according to the type of model (regression or classification) and its architecture.

### Making predictions
Once the model has been trained, you can use it to make predictions by simple call `predict` method.
```python
predictions = model.predict(X)
```

## Beyond the Framework
Apart from the neural network framework, the package also provides:
### Activation functions
<table>
<tr>
    <td><a href="https://en.wikipedia.org/wiki/Sigmoid_function">Sigmoid function</a></td>
    <td><code>sigmoid()</code></td>
</tr>
<tr>
    <td><a href="https://www.medcalc.org/manual/tanh-function.php">Hyperbolic tangent function</a></td>
    <td><code>tanh()</code></td>
</tr>
<tr>
    <td><a href="https://paperswithcode.com/method/relu">Rectified linear unit</a></td>
    <td><code>relu()</code></td>
</tr>
<tr>
    <td><a href="https://paperswithcode.com/method/leaky-relu">Leaky Rectified linear unit</a></td>
    <td><code>leaky_relu()</code></td>
</tr>
<tr>
    <td><a href="https://en.wikipedia.org/wiki/Softmax_function">Softmax function</a></td>
    <td><code>softmax()</code></td>
</tr>
<tr>
    <td><a href="https://paperswithcode.com/method/gelu">Gaussian error linear unit</a></td>
    <td><code>gelu()</code></td>
</tr>
</table>

All above functions have 2 parameters:
* `x`: The input values. Even though some functions can accept numeric primitive data type,
  it is advised to use NumPy array.
* `derivative`: A boolean value indicating whether the function computes the derivative on the input `x`. Default is False.

### Loss functions
<table>
<tr>
    <td><a href="">Logistic loss function</a></td>
    <td><code>log_loss()</code></td>
</tr>
<tr>
    <td><a href="">Cross-entropy loss function</a></td>
    <td><code>cross_entropy_loss()</code></td>
</tr>
<tr>
    <td><a href="">Quadratic loss function</a></td>
    <td><code>quadratic_loss()</code></td>
</tr>
</table>

All above functions have 3 parameters:
* `y_pred`: Predicted labels. It must be a 2D NumPy array and have the same size as `y_true`.
* `y_true`: True labels. It must be a 2D NumPy array and have the same size as `y_pred`.
* `derivative`: A boolean value indicating whether the function computes the derivative. Default is False.

### 2D Decision Boundary
This utility function is used for illustrative purpose. It takes a trained binary classification model, a 2D NumPy input data with 2 attributes, and the corresponding binary label data as input. The function then will plot a 2D decision boundary based on the prediction of the model. \
The input model is not necessarily an instance of **NeuralNetwork**, but it must have `predict`
method that accepts a 2D NumPy array as input.
```python
plot_decision_boundary(model, train_x, train_y)
```
<p align="center">
  <img src="https://github.com/AnhQuoc533/neural-network/blob/master/img/Figure_1.png">
</p>

## License
This project has MIT License, as found in the [LICENSE](LICENSE) file.