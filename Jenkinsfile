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
                        pip install --user -q -r requirements-dev.txt
                        export PATH=$HOME/.local/bin:$PATH
                        black --check src
                        flake8 src
                        pytest tests/ -v
                    '''
                }
            }
        }

        stage('Backend: Build & Tests') {
            // Ce stage a besoin de Java/Maven — image Docker dédiée,
            // même principe que le stage Python : Jenkins orchestre,
            // il n'exécute jamais directement les outils d'une techno.
            agent {
                docker {
                    image 'maven:3.9-eclipse-temurin-17'
                    reuseNode true
                }
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