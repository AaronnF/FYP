import numpy as np

class Activation:
    """Base class for activation functions."""
    def forward(self, Z):
        """
        Computes the forward pass of the activation function.
        Z: Input to the activation function (linear combination WX + b).
        Returns the activated output.
        """
        raise NotImplementedError

    def backward(self, dA_out):
        """
        Computes the backward pass (gradient) of the activation function.
        dA_out: Gradient of the cost with respect to the output of this activation function.
        Returns the gradient of the cost with respect to the input Z of this activation function.
        """
        raise NotImplementedError

class SquareActivation(Activation):
    """Implements the square activation function: f(x) = x^2."""
    def forward(self, Z):
        """Z: input array"""
        self.Z = Z # Store Z for backward pass
        return np.square(Z)

    def backward(self, dA_out):
        """
        dA_out: Gradient from the next layer.
        Returns dA_out * 2 * Z
        """
        if not hasattr(self, 'Z'):
            raise ValueError("Forward pass must be called before backward pass for SquareActivation.")
        return dA_out * 2 * self.Z

class RationalActivation(Activation):
    """Implements a rational activation function: f(x) = x^3 / (x^2 + epsilon)."""
    def __init__(self, epsilon=1e-8):
        self.epsilon = epsilon

    def forward(self, Z):
        """Z: input array"""
        self.Z = Z # Store Z for backward pass
        self.Z_squared = np.square(Z)
        self.denominator_term = self.Z_squared + self.epsilon
        return (Z**3) / self.denominator_term

    def backward(self, dA_out):
        """
        dA_out: Gradient from the next layer.
        Derivative: x^2 * (x^2 + 3*epsilon) / (x^2 + epsilon)^2
        """
        if not hasattr(self, 'Z'):
            raise ValueError("Forward pass must be called before backward pass for RationalActivation.")
        
        numerator_derivative = self.Z_squared * (self.Z_squared + 3 * self.epsilon)
        denominator_derivative = np.square(self.denominator_term)
        
        # Add epsilon to the final denominator for numerical stability, though less critical here
        # as self.denominator_term already has epsilon.
        local_gradient = numerator_derivative / (denominator_derivative + self.epsilon) 
        return dA_out * local_gradient

class ReLU(Activation):
    """Implements the Rectified Linear Unit (ReLU) activation: f(x) = max(0, x)."""
    def forward(self, Z):
        self.Z = Z
        return np.maximum(0, Z)

    def backward(self, dA_out):
        if not hasattr(self, 'Z'):
            raise ValueError("Forward pass must be called before backward pass for ReLU.")
        dZ = np.array(dA_out, copy=True)
        dZ[self.Z <= 0] = 0
        return dZ

class Sigmoid(Activation):
    """Implements the Sigmoid activation: f(x) = 1 / (1 + exp(-x))."""
    def forward(self, Z):
        # Z can be large, np.exp can overflow. Clip Z.
        Z_clipped = np.clip(Z, -500, 500) 
        self.A = 1 / (1 + np.exp(-Z_clipped))
        return self.A

    def backward(self, dA_out):
        if not hasattr(self, 'A'):
            raise ValueError("Forward pass must be called before backward pass for Sigmoid.")
        s = self.A
        return dA_out * s * (1 - s)

class LinearActivation(Activation):
    """Implements a linear activation (identity): f(x) = x."""
    def forward(self, Z):
        self.Z = Z 
        return Z

    def backward(self, dA_out):
        # Derivative is 1
        return dA_out