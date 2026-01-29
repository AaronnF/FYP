#!/usr/bin/env python3
"""
Comprehensive test suite for the Cryptographic DNN implementations.

This file tests all components to ensure they work as expected according to the paper.
"""

import numpy as np
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.crypto_dnn import (
    CryptoDNN, BooleanFunctionDNN, CryptographicPrimitives, AES_SBOX
)
from core.aes_dnn import AESDNN

def test_corner_functions():
    """Test corner function implementation."""
    print("Testing Corner Functions...")
    
    # Test 2-bit XOR corner functions
    # XOR active corners: [0,1] and [1,0]
    corner1 = np.array([0, 1])
    corner2 = np.array([1, 0])
    
    test_cases = [
        (np.array([0, 0]), [0, 0]),  # Should output [0, 0]
        (np.array([0, 1]), [1, 0]),  # Should output [1, 0] 
        (np.array([1, 0]), [0, 1]),  # Should output [0, 1]
        (np.array([1, 1]), [0, 0]),  # Should output [0, 0]
    ]
    
    tolerance = 1e-6
    all_passed = True
    
    for inp, expected in test_cases:
        result1 = CryptoDNN.corner_function(inp, corner1)
        result2 = CryptoDNN.corner_function(inp, corner2)
        
        if not (abs(result1 - expected[0]) < tolerance and abs(result2 - expected[1]) < tolerance):
            print(f"  FAIL: corner_function({inp}) = [{result1:.3f}, {result2:.3f}], expected {expected}")
            all_passed = False
    
    if all_passed:
        print("  PASS: All corner function tests passed")
    
    return all_passed

def test_boolean_functions():
    """Test basic Boolean function implementations."""
    print("Testing Boolean Functions...")
    
    test_inputs = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    
    # Test XOR
    xor_expected = [0, 1, 1, 0]
    xor_results = [CryptographicPrimitives.nnxor(inp) for inp in test_inputs]
    
    xor_passed = all(abs(result - expected) < 1e-6 for result, expected in zip(xor_results, xor_expected))
    
    # Test AND
    and_expected = [0, 0, 0, 1]
    and_results = [CryptographicPrimitives.nnand(inp) for inp in test_inputs]
    
    and_passed = all(abs(result - expected) < 1e-6 for result, expected in zip(and_results, and_expected))
    
    # Test OR
    or_expected = [0, 1, 1, 1]
    or_results = [CryptographicPrimitives.nnor(inp) for inp in test_inputs]
    
    or_passed = all(abs(result - expected) < 1e-6 for result, expected in zip(or_results, or_expected))
    
    if xor_passed:
        print("  PASS: XOR function tests passed")
    else:
        print("  FAIL: XOR function tests failed")
        print(f"    Results: {xor_results}")
        print(f"    Expected: {xor_expected}")
    
    if and_passed:
        print("  PASS: AND function tests passed")
    else:
        print("  FAIL: AND function tests failed")
    
    if or_passed:
        print("  PASS: OR function tests passed")
    else:
        print("  FAIL: OR function tests failed")
    
    return xor_passed and and_passed and or_passed

def test_step_rect_functions():
    """Test STEP and RECT functions."""
    print("Testing STEP and RECT Functions...")
    
    # Test STEP function
    step_test_cases = [
        (0.0, 0.0),
        (1/3, 0.0),
        (0.5, 0.5),
        (2/3, 1.0),
        (1.0, 1.0),
    ]
    
    step_passed = True
    for inp, expected in step_test_cases:
        result = CryptoDNN.step_1_3(inp)
        if abs(result - expected) > 1e-6:
            print(f"  FAIL: STEP_1/3({inp}) = {result:.3f}, expected {expected}")
            step_passed = False
    
    # Test RECT function  
    rect_test_cases = [
        (0.0, 0.0),
        (0.2, 0.6),  # Linear interpolation from 0 to 1/3
        (0.5, 1.0),  # In unsafe range
        (0.8, 0.6),  # Linear interpolation from 2/3 to 1
        (1.0, 0.0),
    ]
    
    rect_passed = True
    for inp, expected in rect_test_cases:
        result = CryptoDNN.rect_1_3(inp)
        # More flexible tolerance for RECT function since it's an approximation
        if abs(result - expected) > 0.2:
            print(f"  FAIL: RECT_1/3({inp}) = {result:.3f}, expected ~{expected}")
            rect_passed = False
    
    if step_passed:
        print("  PASS: STEP function tests passed")
    if rect_passed:
        print("  PASS: RECT function tests passed")
    
    return step_passed and rect_passed

def test_secure_transformation():
    """Test secure blackbox transformation."""
    print("Testing Secure Transformation...")
    
    # Binary inputs should work normally
    binary_inputs = [[0, 0], [0, 1], [1, 0], [1, 1]]
    binary_passed = True
    
    for inp in binary_inputs:
        inp_array = np.array(inp)
        regular_xor = CryptographicPrimitives.nnxor(inp_array)
        secure_xor = CryptographicPrimitives.secure_nnxor(inp_array)
        regular_and = CryptographicPrimitives.nnand(inp_array)
        secure_and = CryptographicPrimitives.secure_nnand(inp_array)
        regular_or = CryptographicPrimitives.nnor(inp_array)
        secure_or = CryptographicPrimitives.secure_nnor(inp_array)
        
        # For binary inputs, secure should give same result as regular
        if abs(regular_xor - secure_xor) > 1e-3:
            print(f"  FAIL: Binary input {inp} - XOR Regular: {regular_xor:.3f}, Secure: {secure_xor:.3f}")
            binary_passed = False
        if abs(regular_and - secure_and) > 1e-3:
            print(f"  FAIL: Binary input {inp} - AND Regular: {regular_and:.3f}, Secure: {secure_and:.3f}")
            binary_passed = False
        if abs(regular_or - secure_or) > 1e-3:
            print(f"  FAIL: Binary input {inp} - OR Regular: {regular_or:.3f}, Secure: {secure_or:.3f}")
            binary_passed = False
    
    # Unsafe inputs should be masked to 0
    unsafe_inputs = [[0.5, 0.5], [0.4, 0.6], [0.45, 0.55]]
    unsafe_passed = True
    
    for inp in unsafe_inputs:
        inp_array = np.array(inp)
        secure_xor = CryptographicPrimitives.secure_nnxor(inp_array)
        secure_and = CryptographicPrimitives.secure_nnand(inp_array)
        secure_or = CryptographicPrimitives.secure_nnor(inp_array)
        
        # Unsafe inputs should be masked to approximately 0
        if abs(secure_xor) > 1e-2:
            print(f"  FAIL: Unsafe input {inp} not masked - XOR Secure: {secure_xor:.3f}")
            unsafe_passed = False
        if abs(secure_and) > 1e-2:
            print(f"  FAIL: Unsafe input {inp} not masked - AND Secure: {secure_and:.3f}")
            unsafe_passed = False
        if abs(secure_or) > 1e-2:
            print(f"  FAIL: Unsafe input {inp} not masked - OR Secure: {secure_or:.3f}")
            unsafe_passed = False
    
    if binary_passed:
        print("  PASS: Binary input handling passed")
    if unsafe_passed:
        print("  PASS: Unsafe input masking passed")
    
    return binary_passed and unsafe_passed

def test_sbox_dnn():
    """Test S-box DNN implementation."""
    print("Testing S-box DNN...")
    
    sbox_dnn = CryptographicPrimitives.create_sbox_dnn(AES_SBOX)
    
    # Test known S-box values
    test_cases = [
        (0x00, 0x63),
        (0x01, 0x7C),
        (0x53, 0xED),
        (0xFF, 0x16),
    ]
    
    sbox_passed = True
    
    for input_byte, expected_byte in test_cases:
        # Convert to binary
        binary_input = np.array([(input_byte >> i) & 1 for i in range(8)])
        
        # Apply S-box
        sbox_output = sbox_dnn(binary_input)
        
        # Convert back to byte
        output_byte = sum(int(round(bit)) * (2**i) for i, bit in enumerate(sbox_output))
        
        if output_byte != expected_byte:
            print(f"  FAIL: S-box(0x{input_byte:02X}) = 0x{output_byte:02X}, expected 0x{expected_byte:02X}")
            sbox_passed = False
    
    if sbox_passed:
        print("  PASS: S-box DNN tests passed")
    
    return sbox_passed

def test_aes_operations():
    """Test AES DNN operations."""
    print("Testing AES Operations...")
    
    aes = AESDNN(128)
    
    # Test bit conversion
    test_bytes = np.array([0x48, 0x65, 0x6C, 0x6C], dtype=np.uint8)  # "Hell"
    bits = aes.bytes_to_bits(test_bytes)
    converted_back = aes.bits_to_bytes(bits)
    
    conversion_passed = np.array_equal(test_bytes, converted_back)
    
    if conversion_passed:
        print("  PASS: Bit conversion tests passed")
    else:
        print("  FAIL: Bit conversion tests failed")
        print(f"    Original: {test_bytes}")
        print(f"    Converted back: {converted_back}")
    
    # Test AddRoundKey (should be XOR)
    state = np.random.randint(0, 256, 16, dtype=np.uint8)
    key = np.random.randint(0, 256, 16, dtype=np.uint8)
    
    state_bits = aes.bytes_to_bits(state)
    key_bits = aes.bytes_to_bits(key)
    
    result_bits = aes.add_round_key(state_bits, key_bits)
    result_bytes = aes.bits_to_bytes(result_bits)
    
    expected = state ^ key  # XOR
    xor_passed = np.array_equal(result_bytes, expected)
    
    if xor_passed:
        print("  PASS: AddRoundKey (XOR) tests passed")
    else:
        print("  FAIL: AddRoundKey (XOR) tests failed")
    
    return conversion_passed and xor_passed

def test_batch_processing():
    """Test batch processing capabilities."""
    print("Testing Batch Processing...")
    
    # Generate batch of random binary inputs
    batch_size = 50
    batch_inputs = np.random.randint(0, 2, (batch_size, 2)).astype(float)
    
    # Compute XOR for the entire batch
    batch_results = CryptographicPrimitives.nnxor(batch_inputs)
    
    # Verify against standard XOR
    expected_results = (batch_inputs[:, 0] + batch_inputs[:, 1]) % 2
    
    # Check accuracy
    matches = np.abs(batch_results - expected_results) < 1e-6
    accuracy = np.mean(matches)
    
    batch_passed = accuracy > 0.95  # Should be near perfect for binary inputs
    
    if batch_passed:
        print(f"  PASS: Batch processing tests passed (accuracy: {accuracy:.1%})")
    else:
        print(f"  FAIL: Batch processing tests failed (accuracy: {accuracy:.1%})")
    
    return batch_passed

def test_real_valued_inputs():
    """Test behavior with real-valued inputs."""
    print("Testing Real-valued Input Handling...")
    
    # Test that natural implementations work on real values
    real_inputs = np.array([
        [0.2, 0.8],
        [0.7, 0.3],
        [0.1, 0.9],
    ])
    
    # These should produce some reasonable output (continuity)
    real_passed = True
    for inp in real_inputs:
        result = CryptographicPrimitives.nnxor(inp)
        # Should be finite and in reasonable range
        if not (np.isfinite(result) and 0 <= result <= 2):
            print(f"  FAIL: Real input {inp} produced unreasonable output: {result}")
            real_passed = False
    
    if real_passed:
        print("  PASS: Real-valued input handling passed")
    
    return real_passed

def run_all_tests():
    """Run all test functions."""
    print("=" * 60)
    print("COMPREHENSIVE CRYPTO-DNN TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Corner Functions", test_corner_functions),
        ("Boolean Functions", test_boolean_functions),
        ("STEP/RECT Functions", test_step_rect_functions),
        ("Secure Transformation", test_secure_transformation),
        ("S-box DNN", test_sbox_dnn),
        ("AES Operations", test_aes_operations),
        ("Batch Processing", test_batch_processing),
        ("Real-valued Inputs", test_real_valued_inputs),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ERROR: Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The implementation is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 
