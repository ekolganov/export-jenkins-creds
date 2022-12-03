// source https://gist.github.com/pedrohdz/41f01dce45b245f3175d19be58ed60af

import jenkins.model.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.impl.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey
import org.jenkinsci.plugins.plaincredentials.impl.FileCredentialsImpl
import org.jenkinsci.plugins.plaincredentials.StringCredentials
import groovy.json.JsonOutput


// set Credentials domain name (null means is it global)
domainName = null

credentialsStore = Jenkins.instance.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0]?.getStore()
domain = new Domain(domainName, null, Collections.<DomainSpecification>emptyList())

def credentials = []
credentialsStore?.getCredentials(domain).each{
  if (it instanceof UsernamePasswordCredentialsImpl)
    credentials += [
      usernamePassword: [
        scope: 'GLOBAL',
        id: it.id,
        username: it.username,
        password: it.password?.getPlainText(),
        description: it.description,
      ]
    ]
  else if (it instanceof BasicSSHUserPrivateKey) {
    data = [
      basicSSHUserPrivateKey: [
        scope: 'GLOBAL',
        id: it.id,
        username: it.username,
        passphrase: it.passphrase ? it.passphrase.getPlainText() : '',
        description: it.description,
        privateKeySource: [
          directEntry: [
            privateKey: it.privateKeySource?.getPrivateKey(),
          ]
        ]
      ]
    ]
    credentials += data
  } 
  else if (it instanceof StringCredentials)
    credentials += [
      string: [
        scope: 'GLOBAL',
        id: it.id,
        secret: it.secret?.getPlainText(),
        description: it.description,
      ]
    ]
  else if (it instanceof FileCredentialsImpl)
    credentials += [
      file: [
        scope: 'GLOBAL',
        id: it.id,
        fileName: it.fileName,
        secretBytes: it.secretBytes?.toString(),
        description: it.description,
      ]
    ]
  else
    credentials += [
      UNKNOWN: [
        id: it.id
      ]
    ]
}

def result = [
  credentials: [   
   credentials
  ]
]
def json = JsonOutput.toJson(result)
println JsonOutput.prettyPrint(json)

return
