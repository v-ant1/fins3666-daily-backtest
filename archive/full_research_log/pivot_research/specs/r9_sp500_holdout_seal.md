# r9 S&P 500 Holdout Seal (L-SEAL2)

The mechanical build completed for 2016-01-04 through 2020-10-30. Membership reconstruction passed; missing adjusted-bar identities are 2/631 (0.317%), below the 3% gate. Member-day price coverage is 99.1419%; as-of SIC2 coverage is 94.0022%. This seal records data construction only and does not authorize opening the holdout to strategy code.

## Artifact hash

- `sealed_holdout_sp500/J2_HOLDOUT.npz` SHA-256: `7b405c9b8348c5c9db794a85480e6c0228901ab96b32d7af4c763ae758c589db`

## Script hashes (SHA-256)

- `build_sealed_holdout.py`: `4b93a6c7750d649141e5b9135f7775b2be294601dbac2a1ab02c5059c13be88f`
- `r6_data/build_sp500_pit.py`: `1b8d5cfa94f47a982bc975110582e2967672cc28e05d5645ac7920ab6c53a334`
- `r6_data/build_sp500_sic_panel.py`: `d90c448e6d77a3f505e7f094fec1545d19438835c3c8958f530217dba7c3948b`
- `sealed_holdout_dow/D7/build_holdout_links.py`: `cd283e2bb3b28841d80ab09878840c9faff3eded8fec4d9e180622cecbc9d2b7`

The builder used GET-only SEC and Alpaca data endpoints. Alpaca settings were SIP daily bars with `adjustment=all`; SEC requests used a generic User-Agent and were throttled below 10 requests/second. Credentials were loaded with python-dotenv from the specified `.env` and were never printed.
