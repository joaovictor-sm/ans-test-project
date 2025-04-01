import { useState } from 'react'

function App() {
  const [busca, setBusca] = useState('')
  const [resultados, setResultados] = useState([])

  // Lista local de operadoras
  const operadoras = [
    { id: 1, nome: 'Vivo', categoria: 'Móvel' },
    { id: 2, nome: 'Claro', categoria: 'Móvel' },
    { id: 3, nome: 'TIM', categoria: 'Móvel' },
    { id: 4, nome: 'Oi', categoria: 'Móvel' },
    { id: 5, nome: 'Nextel', categoria: 'Móvel' },
  ]

  const buscarOperadoras = () => {
    if (!busca) return

    // Filtra localmente as operadoras com base na busca
    const resultadosFiltrados = operadoras.filter(op =>
      op.nome.toLowerCase().includes(busca.toLowerCase())
    )

    setResultados(resultadosFiltrados)
  }

  return (
    <div className="flex flex-col items-center min-h-screen p-5">
      <h1 className="text-2xl font-bold mb-4">Buscar Operadora</h1>

      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Digite o nome da operadora..."
          className="p-2 border rounded-lg"
          value={busca}
          onChange={e => setBusca(e.target.value)}
        />
        <button
          className="bg-blue-500  p-2 rounded-lg"
          onClick={buscarOperadoras}
        >
          Buscar
        </button>
      </div>

      <ul className="mt-5">
        {resultados.length > 0 ? (
          resultados.map(op => (
            <li key={op.id} className="p-2 shadow mb-2 rounded-lg">
              {op.nome} - {op.categoria}
            </li>
          ))
        ) : (
          <p className="text-gray-400 mt-2">Nenhuma operadora encontrada.</p>
        )}
      </ul>
    </div>
  )
}

export default App
