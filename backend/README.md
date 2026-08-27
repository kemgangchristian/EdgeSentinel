# Backend — EdgeSentinel

## Prérequis

**Java 17** (LTS) est requis.

Vérifiez votre version :
```bash
java -version
```

Si absent (macOS) :
```bash
brew install openjdk@17
echo 'export PATH="'$(brew --prefix openjdk@17)'/bin:$PATH"' >> ~/.zshrc
echo 'export JAVA_HOME="'$(brew --prefix openjdk@17)'"' >> ~/.zshrc
source ~/.zshrc
```

## Build et lancement

```bash
./mvnw clean compile
./mvnw spring-boot:run
```

## Tests

```bash
./mvnw test
```
