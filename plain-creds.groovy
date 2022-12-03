// source https://devops.stackexchange.com/a/8692
com.cloudbees.plugins.credentials.SystemCredentialsProvider.getInstance().getCredentials().forEach{
  it.properties.each { prop, val ->
    if (prop == "secretBytes") {
      println(prop + "\n" + new String(com.cloudbees.plugins.credentials.SecretBytes.fromString("${val}").getPlainData()) + "\n")
    } else {
      println(prop + ' = "' + val + '"')
    }
  }
  println("-----------------------")
}
