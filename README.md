# Скрипт предназначен для экспорта кредов из дженкинса и загрузки в vault
Скрипт вытаскивает из дженкинса креды классов и умеет загружать их в vault

- StringCredentialsImpl (парсит и может заргужать в vault)
- UsernamePasswordCredentialsImpl (парсит и может заргужать в vault)
- BasicSSHUserPrivateKey (парсит и может заргужать в vault)
- FileCredentialsImpl (не парсит файлы, но извлекает из jenkins)

## Requirements
установить значения переменных:
- jenkins_url="http://your-jenkins.local/script"
- jenkins_auth_username = "your-jenkins-login"
- jenkins_auth_token = "your-jenkins-login-token"
- vault_url = "your-vault"
- vault_token = "your-vault-token"

```
pip install beautifulsoup4
pip install hvac
```

## Выгрузка FileCredentialsImpl
т.к. .jks файлы выгружаются в corrupted виде, а содержание раличных файлов класса FileCredentialsImpl не уникально для парсинга, то предлагаю выгружать такие файлы самим дженкинсом через подобную джобу и после забирать руками с мастер ноды
```
node("master"){
    stage("asd") {
        creds = [
        "rustore_key_store",
        "ansible_vault",
        "huawei_keyfile",
        "yc_test_cluster_kubeconfig",
        ]
        creds.each {
            withCredentials([file(credentialsId: it, variable: 'keystore_file')]) {
                sh "cat ${keystore_file} > ${keystore_file}"
            }
        }
    }
}
```

## кред вида GoogleServiceAccount
Можно выгрузить следующей джобой с указанием название креда credentialsId
```
import hudson.util.Secret
import com.cloudbees.plugins.credentials.CredentialsProvider
import com.google.jenkins.plugins.credentials.oauth.GoogleRobotPrivateKeyCredentials
import com.google.jenkins.plugins.credentials.oauth.GoogleOAuth2ScopeRequirement

@NonCPS
private def getCredentials(credentialsId) {
    def build = currentBuild.rawBuild
    CredentialsProvider.findCredentialById(
      credentialsId,
      GoogleRobotPrivateKeyCredentials.class,
      build,
      new GoogleOAuth2ScopeRequirement()  {
            @Override
            public Collection<String> getScopes() {
              return null;
            }
          }
      );
}

@NonCPS
private def writeKeyFile(jsonKey) {
    def json
    try {
      json = Secret.decrypt(new String(jsonKey.getPlainData())).getPlainText()
    } catch(Exception e) {
      json = new String(jsonKey.getPlainData())
    }
    writeFile encoding: 'UTF-8', file: '.auth/gcloud.json', text: json
    return pwd() + "/.auth/gcloud.json"
}

@NonCPS
def write(credentialsId = "GoogleServiceAccount") {

  def serviceAccount = getCredentials(credentialsId).getServiceAccountConfig()
  def keyFile = writeKeyFile(serviceAccount.getSecretJsonKey())
  withEnv(["CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE=${keyFile}"]) {
    return ${keyFile}
  }
}

node ("master"){
    stage("asd"){
        key = write()
        sh "cat ./.auth/gcloud.json"
    }
}
```

## преобразование FileCredentialsImpl для vault
т.к. в vault для jenkins нужно закодировать файлы в base64 одну строчку, то оставляю варианты кодирования

### jks файл в одну base64 строку
```
openssl base64 -in key_store_file -out /dev/stdout | tr -d '\n' > encoded_key_store_file
```

### json файл в одну строчку
из json сделать одну строку без base64 кодировки
```
awk -v RS= '{$1=$1}1' json_file > one_string_json_file
```

### json в base64
либо закодирова json в одну строчку, можно воспользоваться ф-ией
```
enc_json(){
file=$1
tmp_file="Temp-0987"
awk -v RS= '{$1=$1}1' $1 > $tmp_file
cat $tmp_file | base64 -i | tr -d '\n' > encoded_$file
rm $tmp_file
}
```