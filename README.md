# Employee Punch Clock

Requires Python 3.12 or newer.

## Set up

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Seed a test employee

The command prompts for the PIN without displaying it:

```bash
python tools/seed_employee.py --employee-number 1001 --first-name Weston --last-name Employee
```

For disposable development environments, the PIN can also be supplied with `--pin`.

## Launch

```bash
python app.py
```

## Administrator access

Enter `8888` on the employee PIN screen to open the administrator sign-in. The initial credentials are username `admin` and password `password`. These are bootstrap credentials and must be replaced before production deployment.

## Run tests

```bash
python -m unittest discover -s tests -v
```
