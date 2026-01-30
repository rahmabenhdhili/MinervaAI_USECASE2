import React, { useState } from 'react';
import styled from 'styled-components';
import { toast } from 'react-toastify';
import { FiDatabase, FiCheckCircle, FiAlertCircle, FiLoader } from 'react-icons/fi';
import { usershopAPI } from '../utils/api';

const LoaderContainer = styled.div`
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(34, 197, 94, 0.1);
  margin-bottom: 2rem;
  border: 1px solid #bbf7d0;
`;

const Title = styled.h3`
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 1.5rem;
  color: #166534;
`;

const LoadButton = styled.button`
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const StepsContainer = styled.div`
  margin-top: 1.5rem;
  max-height: 400px;
  overflow-y: auto;
  background: #f0fdf4;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #bbf7d0;
`;

const Step = styled.div`
  padding: 0.5rem 0;
  font-family: monospace;
  font-size: 0.9rem;
  color: #166534;

  &.success {
    color: #16a34a;
  }

  &.error {
    color: #dc2626;
  }

  &.info {
    color: #15803d;
  }
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
`;

const StatCard = styled.div`
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: white;
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(34, 197, 94, 0.2);
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
`;

const StatLabel = styled.div`
  font-size: 0.9rem;
  opacity: 0.9;
`;

const DataLoader = ({ onLoadComplete }) => {
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState([]);
  const [stats, setStats] = useState(null);

  const handleLoadData = async () => {
    setLoading(true);
    setSteps([]);
    setStats(null);

    try {
      setSteps(['🚀 Démarrage du chargement des données...']);
      
      // Try to load from directory endpoint
      const response = await usershopAPI.loadFromDirectory('data');
      
      // Display all steps
      if (response.data.all_steps) {
        setSteps(response.data.all_steps);
      }

      // Display statistics
      setStats({
        total_products: response.data.total_products,
        files_processed: response.data.files_processed,
        vectors_count: response.data.collection_info?.vectors_count || 0,
        points_count: response.data.collection_info?.points_count || 0
      });

      toast.success(`✅ ${response.data.total_products} produits chargés avec succès !`);
      
      if (onLoadComplete) {
        onLoadComplete(response.data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Erreur inconnue';
      setSteps(prev => [...prev, `❌ Erreur: ${errorMessage}`]);
      toast.error(`Erreur: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const getStepClass = (step) => {
    if (step.includes('✅')) return 'success';
    if (step.includes('❌')) return 'error';
    return 'info';
  };

  return (
    <LoaderContainer>
      <Title>
        <FiDatabase size={24} />
        Chargement Automatique des Données
      </Title>
      
      <LoadButton onClick={handleLoadData} disabled={loading}>
        {loading ? (
          <>
            <FiLoader className="spinner" size={20} />
            Chargement en cours...
          </>
        ) : (
          <>
            <FiDatabase size={20} />
            Charger les produits depuis /data
          </>
        )}
      </LoadButton>

      {stats && (
        <StatsGrid>
          <StatCard>
            <StatValue>{stats.total_products}</StatValue>
            <StatLabel>Produits chargés</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.files_processed}</StatValue>
            <StatLabel>Fichiers traités</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.points_count}</StatValue>
            <StatLabel>Points dans Qdrant</StatLabel>
          </StatCard>
        </StatsGrid>
      )}

      {steps.length > 0 && (
        <StepsContainer>
          {steps.map((step, index) => (
            <Step key={index} className={getStepClass(step)}>
              {step}
            </Step>
          ))}
        </StepsContainer>
      )}
    </LoaderContainer>
  );
};

export default DataLoader;