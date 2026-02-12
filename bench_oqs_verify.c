#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <oqs/oqs.h>

static double now_ms() {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1e6;
}

int main(int argc, char **argv) {
  const char *alg = "ML-DSA-44";
  int iters = 200;
  if (argc >= 2) alg = argv[1];
  if (argc >= 3) iters = atoi(argv[2]);

  if (!OQS_SIG_alg_is_enabled(alg)) {
    fprintf(stderr, "Algorithm not enabled: %s\n", alg);
    return 1;
  }

  OQS_SIG *sig = OQS_SIG_new(alg);
  if (!sig) {
    fprintf(stderr, "Failed to create OQS_SIG for %s\n", alg);
    return 1;
  }

  uint8_t *pk = malloc(sig->length_public_key);
  uint8_t *sk = malloc(sig->length_secret_key);
  uint8_t msg[32];
  uint8_t *signature = malloc(sig->length_signature);
  size_t siglen = 0;

  if (!pk || !sk || !signature) {
    fprintf(stderr, "Allocation failed\n");
    return 1;
  }

  for (int i = 0; i < 32; i++) msg[i] = (uint8_t)i;

  if (OQS_SIG_keypair(sig, pk, sk) != OQS_SUCCESS) {
    fprintf(stderr, "keypair failed\n");
    return 1;
  }

  if (OQS_SIG_sign(sig, signature, &siglen, msg, sizeof(msg), sk) != OQS_SUCCESS) {
    fprintf(stderr, "sign failed\n");
    return 1;
  }

  // warmup
  for (int i = 0; i < 10; i++) {
    if (OQS_SIG_verify(sig, msg, sizeof(msg), signature, siglen, pk) != OQS_SUCCESS) {
      fprintf(stderr, "verify failed (warmup)\n");
      return 1;
    }
  }

  double t0 = now_ms();
  for (int i = 0; i < iters; i++) {
    if (OQS_SIG_verify(sig, msg, sizeof(msg), signature, siglen, pk) != OQS_SUCCESS) {
      fprintf(stderr, "verify failed\n");
      return 1;
    }
  }
  double t1 = now_ms();

  double total = t1 - t0;
  printf("[liboqs %s verify] iters=%d total_ms=%.3f mean_ms=%.6f\n",
         alg, iters, total, total / iters);

  free(pk);
  free(sk);
  free(signature);
  OQS_SIG_free(sig);
  return 0;
}
