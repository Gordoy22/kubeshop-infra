// Conta os pedidos (usado em backup, restauração e evidências).
// A senha é lida do arquivo montado: nunca aparece na linha de comando nem no log.
const fs = require('fs');
const password = fs.readFileSync('/run/secrets/mongo_root_password', 'utf8').trim();
const admin = db.getSiblingDB('admin');
if (!admin.auth('admin', password).ok) quit(1);
print(db.getSiblingDB('kubeshop').orders.countDocuments({}));
