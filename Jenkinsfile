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
            // Maven/Java sont maintenant installés DIRECTEMENT dans
            // l'image Jenkins (infra/jenkins/Dockerfile), pas dans un
            // sous-conteneur Docker séparé. Testcontainers n'a ainsi
            // qu'un seul niveau de Docker-outside-of-Docker à gérer
            // (le conteneur Jenkins parle au démon de l'hôte via le
            // socket monté) -- exactement le pattern que Testcontainers
            // documente et supporte le mieux, contrairement à un
            // conteneur Maven imbriqué en sibling d'un conteneur Jenkins
            // lui-même en sibling du démon hôte (3 niveaux, fragile).
            environment {
                TESTCONTAINERS_RYUK_DISABLED = 'true'
            }
            steps {
                echo "Build et tests du backend Spring Boot"
                sh '''
                    whoami
                    java -version
                    mvn -version
                    docker version
                '''
                dir('backend') {
                    sh '''
                        mvn -B clean verify
                    '''
                }
            }
        }

        stage('Frontend: Build & Lint') {
            // Node.js/npm dans un conteneur dédié, même principe que les
            // stages Python et Java : Jenkins orchestre, chaque techno a
            // son environnement isolé et reproductible.
            agent {
                docker {
                    image 'node:20-slim'
                    reuseNode true
                }
            }
            steps {
                echo "Lint et build du frontend React"
                dir('frontend') {
                    sh '''
                        npm ci
                        npm run lint
                        npm run build
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