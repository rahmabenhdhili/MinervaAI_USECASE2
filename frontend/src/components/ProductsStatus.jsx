import React, { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import { FiAlertCircle, FiCheckCircle, FiDatabase, FiRefreshCw } from 'react-icons/fi';
import { usershopAPI } from '../utils/api';

const pulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
`;

const StatusBanner = styled.div`
  padding: 1.5rem 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: ${pulse} 2s ease-in-out infinite;

  &.warning {
    background: rgba(255, 243, 205, 0.9);
    border: 2px solid #f59e0b;
    color: #92400e;
    box-shadow: 0 8px 32px rgba(245, 158, 11, 0.1);
  }

  &.success {
    background: rgba(245, 254, 251, 0.95);
    border: 2px solid #88c695;
    color: #3f8872;
    box-shadow: 0 8px 32px rgba(63, 136, 114, 0.1);
    animation: none;
  }

  &.loading {
    background: rgba(155, 200, 187, 0.1);
    border: 2px solid #9bc8bb;
    color: #3f8872;
  }
`;

const StatusIcon = styled.div`
  font-size: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
`;

const StatusContent = styled.div`
  flex: 1;
`;

const StatusTitle = styled.div`
  font-weight: 700;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
`;

const StatusMessage = styled.div`
  font-size: 0.95rem;
  opacity: 0.9;
  line-height: 1.5;
`;

const ActionButton = styled.button`
  background: linear-gradient(135deg, #3f8872 0%, #88c695 100%);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(63, 136, 114, 0.3);
  }
`;

const RefreshButton = styled.button`
  background: rgba(255, 255, 255, 0.2);
  color: inherit;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: rotate(180deg);
  }
`;

const ProductsStatus = ({ onLoadData }) => {
  const [status, setStatus] = useState('loading');
  const [productsCount, setProductsCount] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    checkProductsStatus();
  }, []);

  const checkProductsStatus = async () => {
    try {
      setRefreshing(true);
      const response = await usershopAPI.getStats();
      const count = response.data.collection?.points_count || 0;
      setProductsCount(count);
      
      if (count > 0) {
        setStatus('success');
      } else {
        setStatus('warning');
      }
    } catch (error) {
      console.error('Erreur lors de la vérification du statut:', error);
      setStatus('warning');
    } finally {
      setRefreshing(false);
    }
  };

  if (status === 'loading') {
    return (
      <StatusBanner className="loading">
        <StatusIcon>
          <FiDatabase />
        </StatusIcon>
        <StatusContent>
          <StatusTitle>🔍 Vérification des produits...</StatusTitle>
          <StatusMessage>Connexion à la collection "products" en cours</StatusMessage>
        </StatusContent>
      </StatusBanner>
    );
  }

  if (status === 'warning') {
    return (
      <StatusBanner className="warning">
        <StatusIcon>
          <FiAlertCircle />
        </StatusIcon>
        <StatusContent>
          <StatusTitle>⚠️ Collection "products" vide</StatusTitle>
          <StatusMessage>
            Aucun produit trouvé dans la collection Qdrant. 
            Veuillez charger des produits pour utiliser le système de recommandation.
          </StatusMessage>
        </StatusContent>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <RefreshButton onClick={checkProductsStatus} disabled={refreshing}>
            <FiRefreshCw size={16} />
          </RefreshButton>
          {onLoadData && (
            <ActionButton onClick={onLoadData}>
              <FiDatabase size={16} />
              Charger des produits
            </ActionButton>
          )}
        </div>
      </StatusBanner>
    );
  }

  return (
    <StatusBanner className="success">
      <StatusIcon>
        <FiCheckCircle />
      </StatusIcon>
      <StatusContent>
        <StatusTitle>✅ Système prêt</StatusTitle>
        <StatusMessage>
          <strong>{productsCount}</strong> produit{productsCount > 1 ? 's' : ''} disponible{productsCount > 1 ? 's' : ''} 
          dans la collection <strong>"products"</strong>
        </StatusMessage>
      </StatusContent>
      <RefreshButton onClick={checkProductsStatus} disabled={refreshing}>
        <FiRefreshCw size={16} />
      </RefreshButton>
    </StatusBanner>
  );
};

export default ProductsStatus;