import numpy as np

class NeuralNetwork:
    """A simple feed-forward neural network."""
    def __init__(self, loss_fn, optimizer):
        self.layers = []
        self.loss_fn = loss_fn
        self.optimizer = optimizer

    def add_layer(self, layer):
        """Adds a layer to the network."""
        self.layers.append(layer)

    def predict(self, X):
        """
        Performs a forward pass through the network to get predictions.
        X: Input data. Shape: (batch_size, input_features)
        """
        A = X
        for layer in self.layers:
            A = layer.forward(A)
        return A # Final output

    def train(self, X_train, Y_train, epochs, batch_size=32, print_loss_every=10):
        """
        Trains the neural network.
        X_train: Training input data.
        Y_train: Training target data.
        epochs: Number of training iterations over the entire dataset.
        batch_size: Number of samples per gradient update.
        print_loss_every: How often to print the loss.
        """
        num_samples = X_train.shape[0]
        history = [] # To store loss values

        for epoch in range(epochs):
            epoch_loss_accumulator = 0.0
            
            # Shuffle data at the beginning of each epoch
            permutation = np.random.permutation(num_samples)
            X_shuffled = X_train[permutation]
            Y_shuffled = Y_train[permutation]

            for i in range(0, num_samples, batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                Y_batch = Y_shuffled[i:i+batch_size]

                if X_batch.shape[0] == 0: continue # Skip empty batches

                # Forward pass
                Y_pred = self.predict(X_batch)

                # Compute loss
                loss = self.loss_fn.calculate(Y_batch, Y_pred)
                epoch_loss_accumulator += loss * X_batch.shape[0] # Accumulate weighted loss

                # Backward pass
                # Initial gradient from the loss function w.r.t. network output
                dA = self.loss_fn.derivative(Y_batch, Y_pred)

                # Propagate gradient backwards through layers
                for layer in reversed(self.layers):
                    dA = layer.backward(dA)

                # Update weights and biases for all layers
                for layer in self.layers:
                    self.optimizer.update(layer)
            
            avg_epoch_loss = epoch_loss_accumulator / num_samples if num_samples > 0 else 0
            history.append(avg_epoch_loss)
            
            if (epoch + 1) % print_loss_every == 0 or epoch == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_epoch_loss:.6f}")
        
        return history