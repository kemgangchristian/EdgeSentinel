// *******************************************************
// Jenkinsfile — Pipeline CI/CD de EdgeSentinel
//
// Squelette avec les stages de base : checkout, lint/tests, build docker, déploiement conditionnel selon la branche.
// *******************************************************

pipeline {
    agent any

    environment {
        // le registre où seront poussées les images (GitHub Container Registry ici).
        DOCKER_REGISTRY = "ghcr.io/edgesentinel"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Récupération du code source depuis ${env.BRANCH_NAME}"
                checkout scm
            }
        }

        stage('Lint & Tests') {
            // Ce stage a besoin de Python — on utilise une image Docker
            // dédiée plutôt que d'installer Python dans Jenkins lui-même.
            // Jenkins reste un simple orchestrateur ; chaque stage choisit
            // l'environnement adapté à son besoin.
            agent {
                docker {
                    image 'ghcr.io/kemgangchristian/edgesentinel-ci-python:3.11'
                    reuseNode true
                }
            }
            steps {
                echo "Lint et vérification du formatage de l'agent Edge"
                dir('edge') {
                    sh '''
                        export HOME=/tmp
                        export PIP_CACHE_DIR=/tmp/pip-cache
                        pip install --user -q --timeout 60 --retries 3 -r requirements-ci.txt
                        export PATH=$HOME/.local/bin:$PATH
                        black --check src
                        flake8 src
                        pytest tests/ -v
                    '''
                }
            }
        }
                stage('Backend: Build & Tests') {
            // args monte le socket Docker de l'hôte à l'intérieur de ce
            // conteneur Maven, pour que Testcontainers puisse démarrer
            // ses propres conteneurs éphémères (PostgreSQL de test) --
            // même principe Docker-in-Docker que pour Jenkins lui-même.
            agent {
                docker {
                    image 'maven:3.9-eclipse-temurin-17'
                    args '-v /var/run/docker.sock:/var/run/docker.sock'
                    reuseNode true
                }
            }
            // Variable d'environnement injectée par Jenkins lui-même sur
            // tout le processus "sh", garantissant sa transmission jusqu'à
            // la JVM Surefire forkée par Maven pour exécuter les tests
            // (contrairement à un "export" dans le script shell, qui peut
            // se perdre selon comment Maven fork ses sous-process).
            environment {
                TESTCONTAINERS_RYUK_DISABLED = 'true'
                TESTCONTAINERS_HOST_OVERRIDE = 'host.docker.internal'
            }
            steps {
                echo "Build et tests du backend Spring Boot"
                dir('backend') {
                    sh '''
                        ./mvnw -B clean verify
                    '''
                }
            }
        }
        stage('Build Docker') {
            steps {
                echo "[placeholder] Ici viendra le build des images Docker"
            }
        }

        stage('Deploy') {
            steps {
                script {
                    if (env.BRANCH_NAME == 'develop') {
                        echo "[placeholder] Déploiement automatique -> Dev"
                    } else if (env.BRANCH_NAME?.startsWith('release/')) {
                        echo "[placeholder] Déploiement automatique -> Staging"
                    } else if (env.BRANCH_NAME == 'main') {
                        echo "[placeholder] Déploiement -> Prod (approbation manuelle à venir)"
                    } else {
                        echo "Branche ${env.BRANCH_NAME} : pas de déploiement, CI uniquement"
                    }
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline terminé pour la branche ${env.BRANCH_NAME}"
        }
        failure {
            echo "Le pipeline a échoué - [placeholder pour notification Slack/email]"
        }
    }
}