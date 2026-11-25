import { useCallback, useEffect, useRef, useState } from 'react';

// Chama `buscar` agora e a cada `intervaloMs`. Em caso de erro, mantém os últimos dados
// (o painel continua mostrando a última lista enquanto reconecta).
export default function usePolling(buscar, intervaloMs, ativo = true) {
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState(null);
  const buscarRef = useRef(buscar);
  buscarRef.current = buscar;
  const viva = useRef(true);

  const atualizar = useCallback(async () => {
    try {
      const resultado = await buscarRef.current();
      if (viva.current) {
        setDados(resultado);
        setErro(null);
      }
    } catch (e) {
      if (viva.current) setErro(e);
    }
  }, []);

  useEffect(() => {
    viva.current = true;
    if (!ativo) return undefined;
    atualizar();
    const id = setInterval(atualizar, intervaloMs);
    return () => {
      viva.current = false;
      clearInterval(id);
    };
  }, [ativo, intervaloMs, atualizar]);

  return { dados, erro, atualizar };
}
