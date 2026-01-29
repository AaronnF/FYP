import numpy as np

class DenseLayer:
    """A fully connected (dense) layer."""
    def __init__(self, input_size, output_size, activation_fn, W_init_scale=0.01):
        """
        input_size: Number of features from the previous layer.
        output_size: Number of neurons in this layer.
        activation_fn: An instance of an Activation class.
        W_init_scale: Scaling factor for initial weights.
        """
        # Initialize weights with small random values, biases to zero
        self.weights = np.random.randn(input_size, output_size) * W_init_scale
        self.biases = np.zeros((1, output_size))
        self.activation_fn = activation_fn
        
        # Gradients (will be computed during backpropagation)
        self.dW = None
        self.db = None
        self.dA_prev = None # Gradient w.r.t. input of this layer (A_prev)
        
        # Stored values from forward pass (for backpropagation)
        self.A_prev = None # Input to this layer (activations from previous layer)
        self.Z = None      # Linear combination (W @ A_prev + b)

    def forward(self, A_prev):
        """
        Performs the forward pass for this layer.
        A_prev: Activations from the previous layer (or input data).
                Shape: (batch_size, input_size)
        Returns the output of this layer after activation.
        """
        self.A_prev = A_prev
        # Linear step
        self.Z = np.dot(A_prev, self.weights) + self.biases
        # Activation step
        A_curr = self.activation_fn.forward(self.Z)
        return A_curr

    def backward(self, dA_curr):
        """
        Performs the backward pass for this layer.
        dA_curr: Gradient of the loss w.r.t. the output of this layer (A_curr).
                 Shape: (batch_size, output_size)
        Returns the gradient of the loss w.r.t. the input of this layer (dA_prev).
        """
        batch_size = self.A_prev.shape[0]

        # Gradient of loss w.r.t. Z (linear output of this layer before activation)
        # dL/dZ = dL/dA_curr * dA_curr/dZ
        # dA_curr/dZ is the derivative of the activation function (local_gradient)
        dZ = self.activation_fn.backward(dA_curr) # self.Z was input to activation
        # Shape of dZ: (batch_size, output_size)

        # Gradient of loss w.r.t. weights (dW)
        # dL/dW = dL/dZ * dZ/dW. dZ/dW = A_prev.
        self.dW = (1/batch_size) * np.dot(self.A_prev.T, dZ)
        # Shape of dW: (input_size, output_size)

        # Gradient of loss w.r.t. biases (db)
        # dL/db = dL/dZ * dZ/db. dZ/db = 1.
        self.db = (1/batch_size) * np.sum(dZ, axis=0, keepdims=True)
        # Shape of db: (1, output_size)

        # Gradient of loss w.r.t. input of this layer (A_prev for the *next* iteration of backprop)
        # dL/dA_prev = dL/dZ * dZ/dA_prev. dZ/dA_prev = W.
        self.dA_prev = np.dot(dZ, self.weights.T)
        # Shape of dA_prev: (batch_size, input_size)

        return self.dA_prev

# --- Loss Function ---
class MeanSquaredError:
    """Mean Squared Error loss function."""
    def calculate(self, Y_true, Y_pred):
        """
        Calculates the MSE loss.
        Y_true: True target values. Shape: (batch_size, output_size)
        Y_pred: Predicted values. Shape: (batch_size, output_size)
        """
        return np.mean(np.square(Y_true - Y_pred))

    def derivative(self, Y_true, Y_pred):
        """
        Calculates the derivative of MSE loss w.r.t. Y_pred.
        dL/dY_pred = 2 * (Y_pred - Y_true) / N (where N is number of samples in batch)
        """
        if Y_true.shape[0] == 0: return np.zeros_like(Y_pred) # Avoid division by zero for empty batch
        return 2 * (Y_pred - Y_true) / Y_true.shape[0]

# --- Optimizer ---
class SGD:
    """Stochastic Gradient Descent optimizer."""
    def __init__(self, learning_rate=0.01):
        self.learning_rate = learning_rate

    def update(self, layer):
        """Updates the weights and biases of a layer."""
        if hasattr(layer, 'weights') and hasattr(layer, 'biases'): # Ensure it's a layer with parameters
            if layer.dW is not None and layer.db is not None:
                layer.weights -= self.learning_rate * layer.dW
                layer.biases -= self.learning_rate * layer.db
            else:
                # This can happen if a layer's backward pass wasn't called or had issues
                # For simplicity, we'll just skip update if gradients are missing.
                # print(f"Warning: Gradients (dW or db) are None for a layer. Skipping update.")
                pass