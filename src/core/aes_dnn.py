import numpy as np
from typing import List, Tuple
from .crypto_dnn import CryptographicPrimitives, CryptoDNN, AES_SBOX

class AESDNN:
    """
    Advanced Encryption Standard (AES) implementation using Deep Neural Networks.
    
    This implements the AES operations as described in the paper using natural
    DNN implementations and secure transformations.
    """
    
    def __init__(self, key_size: int = 128):
        """
        Initialize AES DNN implementation.
        
        Args:
            key_size: AES key size in bits (128, 192, or 256)
        """
        if key_size not in [128, 192, 256]:
            raise ValueError("Key size must be 128, 192, or 256 bits")
        
        self.key_size = key_size
        self.rounds = {128: 10, 192: 12, 256: 14}[key_size]
        
        # Create AES S-box DNN
        self.sbox_dnn = CryptographicPrimitives.create_sbox_dnn(AES_SBOX)
        
        # AES constants
        self.rcon = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]
    
    def bytes_to_bits(self, byte_array: np.ndarray) -> np.ndarray:
        """Convert array of bytes to bit representation."""
        bits = []
        for byte in byte_array.flatten():
            byte_bits = [(int(byte) >> i) & 1 for i in range(8)]
            bits.extend(byte_bits)
        return np.array(bits)
    
    def bits_to_bytes(self, bit_array: np.ndarray) -> np.ndarray:
        """Convert bit array back to bytes."""
        bit_array = bit_array.flatten()
        if len(bit_array) % 8 != 0:
            raise ValueError("Bit array length must be multiple of 8")
        
        bytes_array = []
        for i in range(0, len(bit_array), 8):
            byte_bits = bit_array[i:i+8]
            byte_val = sum(int(round(bit)) * (2**j) for j, bit in enumerate(byte_bits))
            bytes_array.append(byte_val)
        
        return np.array(bytes_array, dtype=np.uint8)
    
    def add_round_key(self, state_bits: np.ndarray, round_key_bits: np.ndarray, secure: bool = False) -> np.ndarray:
        """
        AddRoundKey operation using DNN XOR.
        
        Args:
            state_bits: 128-bit state as bit array
            round_key_bits: 128-bit round key as bit array 
            secure: Whether to use secure transformation
            
        Returns:
            XORed state as bit array
        """
        if len(state_bits) != 128 or len(round_key_bits) != 128:
            raise ValueError("State and round key must be 128 bits")
        
        # Combine state and key for XOR operation
        combined_input = np.stack([state_bits, round_key_bits], axis=-1)
        
        if secure:
            result = CryptographicPrimitives.secure_nnxor(combined_input)
        else:
            result = CryptographicPrimitives.nnxor(combined_input)
        
        return result
    
    def sub_bytes(self, state_bits: np.ndarray, secure: bool = False) -> np.ndarray:
        """
        SubBytes operation using DNN S-box.
        
        Args:
            state_bits: 128-bit state as bit array
            secure: Whether to use secure transformation
            
        Returns:
            Transformed state as bit array
        """
        if len(state_bits) != 128:
            raise ValueError("State must be 128 bits")
        
        output_bits = []
        
        # Process each byte (8 bits) through S-box
        for i in range(0, 128, 8):
            byte_bits = state_bits[i:i+8]
            
            if secure:
                # Apply secure transformation to individual byte
                def secure_sbox(bits):
                    return self.sbox_dnn(bits)
                sbox_output = CryptoDNN.secure_dnn_forward(byte_bits, secure_sbox)
            else:
                sbox_output = self.sbox_dnn(byte_bits)
            
            output_bits.extend(sbox_output)
        
        return np.array(output_bits)
    
    def shift_rows(self, state_bits: np.ndarray) -> np.ndarray:
        """
        ShiftRows operation - implemented as permutation.
        
        Args:
            state_bits: 128-bit state as bit array
            
        Returns:
            Shifted state as bit array
        """
        if len(state_bits) != 128:
            raise ValueError("State must be 128 bits")
        
        # Convert to 4x4 byte matrix for easier manipulation
        state_bytes = self.bits_to_bytes(state_bits).reshape(4, 4)
        
        # Apply ShiftRows transformation
        # Row 0: no shift
        # Row 1: shift left by 1
        # Row 2: shift left by 2  
        # Row 3: shift left by 3
        shifted = np.zeros_like(state_bytes)
        for row in range(4):
            shifted[row] = np.roll(state_bytes[row], -row)
        
        # Convert back to bits
        return self.bytes_to_bits(shifted)
    
    def galois_multiply(self, a: int, b: int) -> int:
        """Galois field multiplication for MixColumns."""
        result = 0
        for _ in range(8):
            if b & 1:
                result ^= a
            carry = a & 0x80
            a <<= 1
            a &= 0xFF
            if carry:
                a ^= 0x1B  # AES irreducible polynomial
            b >>= 1
        return result
    
    def mix_columns_byte(self, column_bytes: np.ndarray) -> np.ndarray:
        """
        MixColumns operation on a single column using Galois field arithmetic.
        
        Args:
            column_bytes: 4 bytes representing a column
            
        Returns:
            Mixed column as 4 bytes
        """
        # MixColumns matrix multiplication in GF(2^8)
        mix_matrix = np.array([
            [2, 3, 1, 1],
            [1, 2, 3, 1], 
            [1, 1, 2, 3],
            [3, 1, 1, 2]
        ])
        
        result = np.zeros(4, dtype=np.uint8)
        for i in range(4):
            for j in range(4):
                result[i] ^= self.galois_multiply(mix_matrix[i, j], column_bytes[j])
        
        return result
    
    def mix_columns(self, state_bits: np.ndarray) -> np.ndarray:
        """
        MixColumns operation.
        
        Args:
            state_bits: 128-bit state as bit array
            
        Returns:
            Mixed state as bit array
        """
        if len(state_bits) != 128:
            raise ValueError("State must be 128 bits")
        
        # Convert to 4x4 byte matrix
        state_bytes = self.bits_to_bytes(state_bits).reshape(4, 4)
        
        # Apply MixColumns to each column
        mixed_state = np.zeros_like(state_bytes)
        for col in range(4):
            mixed_state[:, col] = self.mix_columns_byte(state_bytes[:, col])
        
        # Convert back to bits
        return self.bytes_to_bits(mixed_state)
    
    def aes_round(self, state_bits: np.ndarray, round_key_bits: np.ndarray, 
                  is_final_round: bool = False, secure: bool = False) -> np.ndarray:
        """
        Complete AES round operation.
        
        Args:
            state_bits: 128-bit state as bit array
            round_key_bits: 128-bit round key as bit array
            is_final_round: Whether this is the final round (no MixColumns)
            secure: Whether to use secure transformations
            
        Returns:
            Transformed state as bit array
        """
        # SubBytes
        state_bits = self.sub_bytes(state_bits, secure)
        
        # ShiftRows
        state_bits = self.shift_rows(state_bits)
        
        # MixColumns (skip in final round)
        if not is_final_round:
            state_bits = self.mix_columns(state_bits)
        
        # AddRoundKey
        state_bits = self.add_round_key(state_bits, round_key_bits, secure)
        
        return state_bits
    
    def key_expansion(self, master_key: np.ndarray) -> List[np.ndarray]:
        """
        Simplified key expansion (for demonstration).
        In practice, this would be implemented using DNNs as well.
        
        Args:
            master_key: Master key as byte array
            
        Returns:
            List of round keys as bit arrays
        """
        # This is a simplified version - full implementation would use DNN operations
        round_keys = []
        
        # Add initial key
        round_keys.append(self.bytes_to_bits(master_key))
        
        # Generate round keys (simplified)
        current_key = master_key.copy()
        for round_num in range(self.rounds):
            # Simplified key schedule - rotate and XOR with round constant
            current_key = np.roll(current_key, -1)
            current_key[0] ^= self.rcon[round_num % len(self.rcon)]
            round_keys.append(self.bytes_to_bits(current_key))
        
        return round_keys
    
    def encrypt_block(self, plaintext: np.ndarray, master_key: np.ndarray, secure: bool = False) -> np.ndarray:
        """
        Encrypt a single 128-bit block using AES.
        
        Args:
            plaintext: 16-byte plaintext block
            master_key: AES master key (16, 24, or 32 bytes)
            secure: Whether to use secure transformations
            
        Returns:
            16-byte ciphertext block
        """
        if len(plaintext) != 16:
            raise ValueError("Plaintext must be exactly 16 bytes")
        
        expected_key_size = self.key_size // 8
        if len(master_key) != expected_key_size:
            raise ValueError(f"Master key must be {expected_key_size} bytes for {self.key_size}-bit AES")
        
        # Convert to bit representation
        state_bits = self.bytes_to_bits(plaintext)
        
        # Generate round keys
        round_keys = self.key_expansion(master_key)
        
        # Initial AddRoundKey
        state_bits = self.add_round_key(state_bits, round_keys[0], secure)
        
        # Main rounds
        for round_num in range(1, self.rounds + 1):
            is_final = (round_num == self.rounds)
            state_bits = self.aes_round(state_bits, round_keys[round_num], is_final, secure)
        
        # Convert back to bytes
        return self.bits_to_bytes(state_bits)
    
    def decrypt_block(self, ciphertext: np.ndarray, master_key: np.ndarray, secure: bool = False) -> np.ndarray:
        """
        Decrypt a single 128-bit block using AES.
        Note: This is a placeholder - full implementation would require inverse operations.
        
        Args:
            ciphertext: 16-byte ciphertext block
            master_key: AES master key
            secure: Whether to use secure transformations
            
        Returns:
            16-byte plaintext block
        """
        # This would require implementing inverse operations (InvSubBytes, InvShiftRows, etc.)
        # For now, we'll just return the input as a placeholder
        print("Decryption not fully implemented - would require inverse S-box and operations")
        return ciphertext


class AESDemo:
    """Demonstration class for AES DNN operations."""
    
    @staticmethod
    def test_aes_components():
        """Test individual AES components."""
        print("Testing AES DNN Components")
        print("=" * 50)
        
        aes = AESDNN(128)
        
        # Test data
        test_state = np.random.randint(0, 256, 16, dtype=np.uint8)
        test_key = np.random.randint(0, 256, 16, dtype=np.uint8)
        
        print(f"Original state: {test_state.hex()}")
        
        # Convert to bits
        state_bits = aes.bytes_to_bits(test_state)
        key_bits = aes.bytes_to_bits(test_key)
        
        # Test AddRoundKey
        print("\n1. Testing AddRoundKey:")
        ark_result = aes.add_round_key(state_bits, key_bits)
        ark_bytes = aes.bits_to_bytes(ark_result)
        print(f"After AddRoundKey: {ark_bytes.hex()}")
        
        # Test SubBytes
        print("\n2. Testing SubBytes:")
        sb_result = aes.sub_bytes(state_bits)
        sb_bytes = aes.bits_to_bytes(sb_result)
        print(f"After SubBytes: {sb_bytes.hex()}")
        
        # Test ShiftRows
        print("\n3. Testing ShiftRows:")
        sr_result = aes.shift_rows(state_bits)
        sr_bytes = aes.bits_to_bytes(sr_result)
        print(f"After ShiftRows: {sr_bytes.hex()}")
        
        # Test MixColumns
        print("\n4. Testing MixColumns:")
        mc_result = aes.mix_columns(state_bits)
        mc_bytes = aes.bits_to_bytes(mc_result)
        print(f"After MixColumns: {mc_bytes.hex()}")
    
    @staticmethod
    def test_full_encryption():
        """Test full AES encryption."""
        print("\n" + "=" * 50)
        print("Testing Full AES Encryption")
        print("=" * 50)
        
        aes = AESDNN(128)
        
        # Test vectors
        plaintext = b"Hello, World!123"  # 16 bytes
        key = b"SecretKey1234567"        # 16 bytes
        
        plaintext_array = np.frombuffer(plaintext, dtype=np.uint8)
        key_array = np.frombuffer(key, dtype=np.uint8)
        
        print(f"Plaintext:  {plaintext}")
        print(f"Key:        {key}")
        print(f"Plaintext (hex): {plaintext_array.hex()}")
        print(f"Key (hex):       {key_array.hex()}")
        
        # Encrypt
        print("\nEncrypting...")
        ciphertext = aes.encrypt_block(plaintext_array, key_array, secure=False)
        print(f"Ciphertext (hex): {ciphertext.hex()}")
        
        # Test with secure transformation
        print("\nEncrypting with secure transformation...")
        secure_ciphertext = aes.encrypt_block(plaintext_array, key_array, secure=True)
        print(f"Secure ciphertext (hex): {secure_ciphertext.hex()}")
    
    @staticmethod
    def run_demo():
        """Run the complete AES demo."""
        AESDemo.test_aes_components()
        AESDemo.test_full_encryption()


if __name__ == "__main__":
    AESDemo.run_demo() 