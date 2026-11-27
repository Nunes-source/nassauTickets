import { useState } from 'react';
import { entrar } from '../api/api.js';
import { textoDoErro } from '../api/cliente.js';

export default function LoginAtendente({ aoEntrar, aviso }) {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  async function enviar(evento) {
    evento.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const dados = await entrar(email.trim(), senha);
      aoEntrar({ token: dados.access_token, nome: dados.nome, perfil: dados.perfil });
    } catch (e) {
      setErro(textoDoErro(e));
      setEnviando(false);
    }
  }

  return (
    <section>
      <h1>Terminal do atendente</h1>
      <form className="cartao login" onSubmit={enviar}>
        <p className="subtitulo">Entre com o seu e-mail e a sua senha.</p>
        {aviso && <p role="status" className="aviso aviso-info">{aviso}</p>}
        <label className="campo">
          E-mail
          <input type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="campo">
          Senha
          <input type="password" autoComplete="current-password" required value={senha} onChange={(e) => setSenha(e.target.value)} />
        </label>
        {erro && <p role="alert" className="aviso aviso-erro">{erro}</p>}
        <button className="botao-primario" type="submit" disabled={enviando}>
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
    </section>
  );
}
