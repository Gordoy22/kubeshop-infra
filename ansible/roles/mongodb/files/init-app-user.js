// Executado pela imagem oficial do MongoDB apenas na PRIMEIRA inicialização
// (diretório de dados vazio). Cria o usuário da aplicação com permissão mínima
// (readWrite apenas no banco kubeshop). Mesmo comportamento do docker/mongodb/init.js
// do repositório original do KubeShop.
const fs = require('fs');
const appDb = db.getSiblingDB('kubeshop');
appDb.createUser({
  user: process.env.MONGO_APP_USERNAME,
  pwd: fs.readFileSync(process.env.MONGO_APP_PASSWORD_FILE, 'utf8').trim(),
  roles: [{ role: 'readWrite', db: 'kubeshop' }],
});
