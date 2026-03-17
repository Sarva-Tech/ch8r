# Polymorphic Dispatch — OOP Essentials

## The Problem: Rigid Code

Imagine you have different kinds of things that behave similarly, but not exactly the same.
Without polymorphic dispatch, you end up with long `if/else` chains that grow every time you add a new type.

```python
# fragile — every new animal means editing this function
def make_sound(animal_type):
    if animal_type == 'dog':
        print('woof')
    elif animal_type == 'cat':
        print('meow')
    # ... add another elif for each animal
```

You don't need to know OOP theory — just notice the pain.

---

## The Solution: A Promise (Contract)

We want each object to own its behaviour. Polymorphism means "many forms" — we just need a common guarantee: every animal knows how to `speak`.

In Python we agree on method names — no formal interface required.

```python
# a "contract" — if you have a .speak() method, you're an animal
class Dog:
    def speak(self):
        print('woof')

class Cat:
    def speak(self):
        print('meow')
```

Both objects dispatch polymorphically: the caller doesn't check type, it just calls `.speak()`.

---

## Polymorphic Call = No Conditionals

Write one function that works for any object that follows the contract.

```python
def perform_speak(animal):
    animal.speak()  # dispatch — dynamic decision

dog = Dog()
cat = Cat()

perform_speak(dog)  # woof
perform_speak(cat)  # meow

# add a new animal without touching existing code
class Bird:
    def speak(self):
        print('chirp')

perform_speak(Bird())  # chirp
```

This is the heart of polymorphic dispatch: **same call, different behaviour**.

---

## Classes and Inheritance (Clean at Scale)

A base class makes the contract explicit and lets subclasses share logic.

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        raise NotImplementedError('subclass must implement')  # "abstract"

class Dog(Animal):
    def speak(self):
        print(f'{self.name} says woof')

class Cat(Animal):
    def speak(self):
        print(f'{self.name} says meow')

animals = [Dog('Bella'), Cat('Luna')]
for a in animals:
    a.speak()
# Bella says woof
# Luna says meow
```

No type checks, no switches — adding a new `Cow` doesn't break anything.

---

## Production-Ready: Payment Processors

E-commerce: different payment gateways. Polymorphism keeps it rock solid.

```python
class PayPalProcessor:
    def process(self, amount):
        return f'PayPal: charged ${amount}'

class StripeProcessor:
    def process(self, amount):
        return f'Stripe: charged ${amount} (fee 2.9%)'

class CashProcessor:
    def process(self, amount):
        return f'Cash: collect ${amount} (no fee)'

# checkout — completely open to new processors
def checkout(payment_method, amount):
    print(payment_method.process(amount))

checkout(PayPalProcessor(), 99)
checkout(StripeProcessor(), 45)
checkout(CashProcessor(), 20)
```

New `CryptoProcessor`? Just pass it. Zero changes in `checkout`.

---

## Polymorphism Without Inheritance

You don't even need a base class. As long as the method name matches, dispatch works.

```python
class Logger:
    def log(self, msg):
        print(msg)

class AlertSystem:
    def log(self, msg):
        print(f'ALERT: {msg}')

def write(device, message):
    device.log(message)  # polymorphic dispatch

write(Logger(), 'server started')     # server started
write(AlertSystem(), 'CPU overload')  # ALERT: CPU overload
```

---

## Real-World Example: Notification Provider Validation

Our app supports multiple notification providers — email, Slack, Discord — each with its own validation rules. This is exactly the problem polymorphic dispatch solves.

### Before — rigid, growing if/elif

```python
# every new provider means editing this function
def validate_config_for_type(provider_type, config):
    if provider_type == 'email':
        email = config.get('email', '').strip()
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise ValidationError(...)

    if provider_type in ('slack', 'discord'):
        url = config.get('webhookUrl', '').strip()
        if not url.startswith(('http://', 'https://')):
            raise ValidationError(...)
        if provider_type == 'slack' and 'hooks.slack.com' not in url:
            raise ValidationError(...)
        if provider_type == 'discord' and 'discord.com' not in url:
            raise ValidationError(...)
```

### After — each provider owns its rules

```python
# contract: every validator implements .validate(config)
class BaseProviderValidator:
    def validate(self, config): pass

class EmailProviderValidator(BaseProviderValidator):
    def validate(self, config):
        email = config.get('email', '').strip()
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise ValidationError(...)

class WebhookProviderValidator(BaseProviderValidator):
    webhook_domain = None  # subclasses set this

    def validate(self, config):
        url = config.get('webhookUrl', '').strip()
        if not url.startswith(('http://', 'https://')):
            raise ValidationError(...)
        if self.webhook_domain and self.webhook_domain not in url:
            raise ValidationError(...)

class SlackProviderValidator(WebhookProviderValidator):
    webhook_domain = 'hooks.slack.com'

class DiscordProviderValidator(WebhookProviderValidator):
    webhook_domain = 'discord.com'

# registry maps type → validator
_VALIDATOR_REGISTRY = {
    'email':   EmailProviderValidator(),
    'slack':   SlackProviderValidator(),
    'discord': DiscordProviderValidator(),
}

# dispatcher — never changes
def validate_config_for_type(provider_type, config):
    # ... shared guards (dict check, required fields) ...
    validator = _VALIDATOR_REGISTRY.get(provider_type, BaseProviderValidator())
    validator.validate(config)  # polymorphic dispatch — no if/elif on type
```

Adding Teams is two lines, nothing else changes:

```python
class TeamsProviderValidator(WebhookProviderValidator):
    webhook_domain = 'webhook.office.com'

_VALIDATOR_REGISTRY['teams'] = TeamsProviderValidator()
```

---

## Your Polymorphic Toolkit

1. Define a contract (method name + signature) — informally or via a base class
2. Implement the contract in each concrete class
3. Call the method without checking type — let Python dispatch it
4. Extend forever: new implementations, zero changes to existing code
