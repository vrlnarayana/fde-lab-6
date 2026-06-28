// main.bicep  —  Britannia: EU/UK-resident, keyless Azure OpenAI
param location string = 'westeurope'        // residency: EU/UK only
param aoaiName string
param deploymentName string = 'gpt-4o-mini'
var openAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'  // Cognitive Services OpenAI User

resource aoai 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: aoaiName
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: aoaiName    // required for Entra ID auth
    disableLocalAuth: true           // keyless only
    publicNetworkAccess: 'Enabled'   // laptop lab; production Britannia = 'Disabled' + private endpoint
  }
}

resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aoai
  name: deploymentName
  sku: { name: 'DataZoneStandard', capacity: 10 }
  properties: { model: { format: 'OpenAI', name: 'gpt-4o-mini', version: '2024-07-18' } }
}

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${aoaiName}-app-id'
  location: location
}

resource ra 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aoai.id, uami.id, openAiUserRoleId)
  scope: aoai
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openAiUserRoleId)
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output endpoint string = aoai.properties.endpoint
output deploymentName string = deployment.name
output appClientId string = uami.properties.clientId
