// *******************************************************
// basic-security.groovy — Sécurisation minimale de Jenkins au démarrage
// Exécuté automatiquement par Jenkins (dossier init.groovy.d).
// *******************************************************

import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()

// Les identifiants viennent des variables d'environnement du conteneur
// (définies dans infra/jenkins/.env, jamais en dur ici).
def adminUser = System.getenv("JENKINS_ADMIN_USER") ?: "admin"
def adminPassword = System.getenv("JENKINS_ADMIN_PASSWORD")

if (adminPassword == null || adminPassword.isEmpty()) {
    println "⚠️  JENKINS_ADMIN_PASSWORD non défini — sécurisation ignorée."
    return
}

def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount(adminUser, adminPassword)
instance.setSecurityRealm(hudsonRealm)

// Stratégie d'autorisation : seuls les utilisateurs authentifiés ont accès,
// et uniquement l'administrateur a les pleins droits. Aucun accès anonyme.
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

instance.save()
println "✅ Sécurité Jenkins configurée : utilisateur '${adminUser}' créé, accès anonyme désactivé."
