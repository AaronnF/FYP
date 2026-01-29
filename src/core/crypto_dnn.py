import numpy as np
from itertools import product
from typing import List, Tuple, Callable, Union

class CryptoDNN:
    """
    Implementation of cryptographic primitives using Deep Neural Networks
    based on the paper's natural implementations and secure transformations.
    """
    
    @staticmethod
    def corner_function(x: np.ndarray, b: np.ndarray, c: float = 0.5) -> np.ndarray:
        """
        Implements the corner function for a specific binary corner.
        
        Args:
            x: Input vector(s) of shape (..., k)
            b: Binary corner vector of shape (k,)
            c: Small positive constant (default 0.5)
            
        Returns:
            Corner function value(s)
        """
        x = np.asarray(x)
        b = np.asarray(b)
        
        if x.shape[-1] != b.shape[0]:
            raise ValueError(f"Input dimension {x.shape[-1]} doesn't match corner dimension {b.shape[0]}")
        
        # Calculate: sum(x_i for i where b_i=1) + sum((1-x_i) for i where b_i=0) - k + c
        term1 = np.sum(x * b, axis=-1)  # sum of x_i where b_i=1
        term2 = np.sum((1 - x) * (1 - b), axis=-1)  # sum of (1-x_i) where b_i=0
        linear_combination = term1 + term2 - b.shape[0] + c
        
        # Apply ReLU and scale by 1/c
        return np.maximum(0, linear_combination / c)
    
    @staticmethod
    def sum_of_corners(x: np.ndarray, active_corners: List[np.ndarray], c: float = 0.5) -> np.ndarray:
        """
        Implements the sum of corners for a Boolean function.
        
        Args:
            x: Input vector(s) of shape (..., k)
            active_corners: List of binary vectors representing active corners
            c: Small positive constant
            
        Returns:
            Sum of corner functions
        """
        if not active_corners:
            return np.zeros(x.shape[:-1])
        
        result = np.zeros(x.shape[:-1])
        for corner in active_corners:
            result += CryptoDNN.corner_function(x, corner, c)
        
        return result
    
    @staticmethod
    def vectorial_sum_of_corners(x: np.ndarray, active_corners_list: List[List[np.ndarray]], c: float = 0.5) -> np.ndarray:
        """
        Implements vectorial Boolean functions using concatenated sum of corners.
        
        Args:
            x: Input vector(s) of shape (..., k)
            active_corners_list: List of lists, each containing active corners for one output bit
            c: Small positive constant
            
        Returns:
            Array of shape (..., m) where m is the number of output bits
        """
        outputs = []
        for corners in active_corners_list:
            outputs.append(CryptoDNN.sum_of_corners(x, corners, c))
        
        return np.stack(outputs, axis=-1)
    
    @staticmethod
    def step_1_3(x: np.ndarray) -> np.ndarray:
        """
        Implements the STEP_{1/3} function for input/output sanitization.
        STEP_{1/3}(x) = 3 * (ReLU(x - 1/3) - ReLU(x - 2/3))
        
        Args:
            x: Input values
            
        Returns:
            Sanitized values (0 for x < 1/3, 1 for x > 2/3, linear interpolation between)
        """
        x = np.asarray(x)
        return 3 * (np.maximum(0, x - 1/3) - np.maximum(0, x - 2/3))
    
    @staticmethod
    def rect_1_3(x: np.ndarray) -> np.ndarray:
        """
        Implements the RECT_{1/3} function for detecting unsafe inputs.
        Returns 1 for x in [1/3, 2/3], 0 for x <= 0 or x >= 1, linear interpolation elsewhere.
        
        Args:
            x: Input values
            
        Returns:
            Rectangle function values
        """
        # Convert to numpy array to handle both scalars and arrays
        x = np.asarray(x)
        original_shape = x.shape
        x = np.atleast_1d(x)
        
        # This is a simplified approximation of the RECT function
        # It outputs 1 for values in the "unsafe" range [1/3, 2/3]
        mask1 = (x >= 1/3) & (x <= 2/3)
        mask2 = (x > 0) & (x < 1/3)
        mask3 = (x > 2/3) & (x < 1)
        
        result = np.zeros_like(x)
        result[mask1] = 1.0  # Unsafe range
        result[mask2] = 3 * x[mask2]  # Linear interpolation from 0 to 1/3
        result[mask3] = 3 * (1 - x[mask3])  # Linear interpolation from 2/3 to 1
        
        # Return in original shape
        return result.reshape(original_shape) if original_shape else result.item()
    
    @staticmethod
    def secure_dnn_forward(p: np.ndarray, dnn_func: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
        """
        Applies the secure blackbox transformation (DS) to a DNN implementation.
        
        Args:
            p: Input vector(s)
            dnn_func: Function implementing the DNN cryptographic primitive
            
        Returns:
            Secure output (0 for unsafe inputs, expected binary output for safe inputs)
        """
        # Step 1: Input sanitization
        p_sanitized = CryptoDNN.step_1_3(p)
        
        # Step 2: DNN computation
        c = dnn_func(p_sanitized)
        
        # Step 3: Output sanitization
        c_sanitized = CryptoDNN.step_1_3(c)
        
        # Step 4: Compute mask (sum of RECT over all inputs)
        rect_values = CryptoDNN.rect_1_3(p_sanitized)
        if p_sanitized.ndim > 0:
            mask = np.sum(rect_values)
        else:
            mask = rect_values
        
        # Step 5: Apply mask with final ReLU
        return np.maximum(0, c_sanitized - mask)


class BooleanFunctionDNN:
    """Helper class for generating active corners for common Boolean functions."""
    
    @staticmethod
    def get_active_corners(k: int, func: Callable[[Tuple[int, ...]], int]) -> List[np.ndarray]:
        """
        Generate active corners for a Boolean function.
        
        Args:
            k: Number of input bits
            func: Boolean function that takes a tuple of k bits and returns 0 or 1
            
        Returns:
            List of binary vectors representing active corners
        """
        active_corners = []
        for bits in product([0, 1], repeat=k):
            if func(bits) == 1:
                active_corners.append(np.array(bits))
        return active_corners
    
    @staticmethod
    def xor_function(bits: Tuple[int, ...]) -> int:
        """XOR function."""
        return sum(bits) % 2
    
    @staticmethod
    def and_function(bits: Tuple[int, ...]) -> int:
        """AND function."""
        return int(all(bits))
    
    @staticmethod
    def or_function(bits: Tuple[int, ...]) -> int:
        """OR function."""
        return int(any(bits))
    
    @staticmethod
    def get_xor_active_corners(k: int) -> List[np.ndarray]:
        """Get active corners for k-bit XOR."""
        return BooleanFunctionDNN.get_active_corners(k, BooleanFunctionDNN.xor_function)
    
    @staticmethod
    def get_and_active_corners(k: int) -> List[np.ndarray]:
        """Get active corners for k-bit AND."""
        return BooleanFunctionDNN.get_active_corners(k, BooleanFunctionDNN.and_function)
    
    @staticmethod
    def get_or_active_corners(k: int) -> List[np.ndarray]:
        """Get active corners for k-bit OR."""
        return BooleanFunctionDNN.get_active_corners(k, BooleanFunctionDNN.or_function)


class CryptographicPrimitives:
    """Implementation of specific cryptographic primitives using DNNs."""
    
    @staticmethod
    def nnxor(x: np.ndarray, c: float = 0.5) -> np.ndarray:
        """
        Natural DNN implementation of XOR.
        
        Args:
            x: Input bits of shape (..., k)
            c: Corner function parameter
            
        Returns:
            XOR result
        """
        k = x.shape[-1]
        active_corners = BooleanFunctionDNN.get_xor_active_corners(k)
        return CryptoDNN.sum_of_corners(x, active_corners, c)
    
    @staticmethod
    def secure_nnxor(x: np.ndarray, c: float = 0.5) -> np.ndarray:
        """Secure XOR implementation with DS transformation."""
        def xor_func(p):
            return CryptographicPrimitives.nnxor(p, c)
        return CryptoDNN.secure_dnn_forward(x, xor_func)
    
    @staticmethod
    def nnand(x: np.ndarray, c: float = 0.5) -> np.ndarray:
        """Natural DNN implementation of AND."""
        k = x.shape[-1]
        active_corners = BooleanFunctionDNN.get_and_active_corners(k)
        return CryptoDNN.sum_of_corners(x, active_corners, c)

    @staticmethod
    def secure_nnand(x: np.ndarray, c: float = 0.5) -> np.ndarray:
        """Secure AND implementation with DS transformation."""
        def and_func(p):
            return CryptographicPrimitives.nnand(p, c)
        return CryptoDNN.secure_dnn_forward(x, and_func)
    
    @staticmethod
    def nnor(x: np.ndarray, c: float = 0.5) -> np.ndarray:
        """Natural DNN implementation of OR."""
        k = x.shape[-1]
        active_corners = BooleanFunctionDNN.get_or_active_corners(k)
        return CryptoDNN.sum_of_corners(x, active_corners, c)

    @staticmethod
    def secure_nnor(x: np.ndarray, c: float = 0.5) -> np.ndarray:
        """Secure OR implementation with DS transformation."""
        def or_func(p):
            return CryptographicPrimitives.nnor(p, c)
        return CryptoDNN.secure_dnn_forward(x, or_func)
    
    @staticmethod
    def create_sbox_dnn(sbox_table: List[int]) -> Callable[[np.ndarray], np.ndarray]:
        """
        Creates a DNN implementation of an S-box.
        
        Args:
            sbox_table: List of 256 values representing the S-box lookup table
            
        Returns:
            Function that computes S-box using DNN
        """
        if len(sbox_table) != 256:
            raise ValueError("S-box table must have exactly 256 entries")
        
        # Generate active corners for each output bit
        active_corners_list = []
        for bit_pos in range(8):  # 8 output bits
            corners = []
            for input_val in range(256):
                output_val = sbox_table[input_val]
                if (output_val >> bit_pos) & 1:  # Check if this bit is 1
                    # Convert input_val to 8-bit binary vector
                    binary_input = np.array([(input_val >> i) & 1 for i in range(8)])
                    corners.append(binary_input)
            active_corners_list.append(corners)
        
        def sbox_dnn(x: np.ndarray, c: float = 0.5) -> np.ndarray:
            return CryptoDNN.vectorial_sum_of_corners(x, active_corners_list, c)
        
        return sbox_dnn


# AES S-box for demonstration
AES_SBOX = [
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
    0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
    0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
    0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
    0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
    0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
    0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
    0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
    0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
    0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
    0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
    0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
    0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
    0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
    0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16
] 
