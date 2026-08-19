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
            steps {
                echo "[placeholder] Ici viendront black/flake8/pytest pour l'agent Edge"
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