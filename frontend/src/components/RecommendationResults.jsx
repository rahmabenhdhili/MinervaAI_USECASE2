import React, { useState } from 'react';
import styled from 'styled-components';
import ProductCard from './ProductCard';
import ProductComparison from './ProductComparison';
import { FiStar, FiInfo } from 'react-icons/fi';

const ResultsContainer = styled.div`
  margin-top: 2rem;
`;

const StatsBar = styled.div`
  background: #f5fefb;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
  align-items: center;
  border: 1px solid #9bc8bb;
`;

const StatItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
`;

const StatLabel = styled.span`
  font-size: 0.85rem;
  color: #3f8872;
  font-weight: 500;
`;

const StatValue = styled.span`
  font-size: 1.2rem;
  color: #3f8872;
  font-weight: 700;
`;

const CompareBar = styled.div`
  background: linear-gradient(135deg, #51ae93 0%, #3f8872 100%);
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 6px rgba(81, 174, 147, 0.2);
`;

const CompareInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const CompareButton = styled.button`
  background: white;
  color: #51ae93;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 255, 255, 0.3);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const ClearButton = styled.button`
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid white;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
`;

const Section = styled.div`
  margin-bottom: 3rem;
`;

const SectionTitle = styled.h2`
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 1.5rem;
  color: #3f8872;
  font-size: 1.5rem;
`;

const DescriptionCard = styled.div`
  background: linear-gradient(135deg, #51ae93 0%, #3f8872 100%);
  color: white;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px rgba(81, 174, 147, 0.2);
`;

const DescriptionTitle = styled.h3`
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 10px;
`;

const DescriptionText = styled.p`
  line-height: 1.6;
  font-size: 1.1rem;
`;

const ProductGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
`;

const NoResults = styled.div`
  text-align: center;
  padding: 3rem;
  color: #3f8872;
  background: #f5fefb;
  border-radius: 12px;
  border: 1px solid #9bc8bb;
`;

const RecommendationResults = ({ results }) => {
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [showComparison, setShowComparison] = useState(false);

  if (!results) {
    return null;
  }

  const { product_description, recommendations, total_found, total_after_filter } = results;

  const handleProductSelect = (product) => {
    setSelectedProducts(prev => {
      // Si déjà sélectionné, le retirer
      if (prev.find(p => p.name === product.name)) {
        return prev.filter(p => p.name !== product.name);
      }
      // Si moins de 2 produits, ajouter
      if (prev.length < 2) {
        return [...prev, product];
      }
      // Si 2 produits déjà sélectionnés, remplacer le premier
      return [prev[1], product];
    });
    setShowComparison(false);
  };

  const handleCompare = () => {
    if (selectedProducts.length === 2) {
      setShowComparison(true);
    }
  };

  const handleClearSelection = () => {
    setSelectedProducts([]);
    setShowComparison(false);
  };

  const handleCloseComparison = () => {
    setShowComparison(false);
  };

  // Utiliser l'ID du produit depuis la base de données
  const getProductId = (product) => {
    return product.id || `${product.name}_${product.price}`.replace(/[^a-zA-Z0-9]/g, '_');
  };

  return (
    <ResultsContainer>
      {/* Statistiques de recherche */}
      {(total_found || total_after_filter) && (
        <StatsBar>
          <StatItem>
            <StatLabel>🔍 Products Found</StatLabel>
            <StatValue>{total_found || 0}</StatValue>
          </StatItem>
          <StatItem>
            <StatLabel>💰 After Price Filter</StatLabel>
            <StatValue>{total_after_filter || 0}</StatValue>
          </StatItem>
          <StatItem>
            <StatLabel>📋 Displayed</StatLabel>
            <StatValue>{recommendations?.length || 0}</StatValue>
          </StatItem>
        </StatsBar>
      )}

      {/* Barre de comparaison */}
      {recommendations && recommendations.length > 1 && (
        <CompareBar>
          <CompareInfo>
            <span style={{ fontSize: '1.5rem' }}>⚖️</span>
            <div>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                🌿 Comparison Tool
              </div>
              <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>
                {selectedProducts.length === 0 && 'Select 2 products to compare'}
                {selectedProducts.length === 1 && `1 product selected - Select another one`}
                {selectedProducts.length === 2 && `2 products selected - Ready to compare!`}
              </div>
            </div>
          </CompareInfo>
          <div style={{ display: 'flex', gap: '1rem' }}>
            {selectedProducts.length > 0 && (
              <ClearButton onClick={handleClearSelection}>
                Clear
              </ClearButton>
            )}
            <CompareButton
              onClick={handleCompare}
              disabled={selectedProducts.length !== 2}
            >
              Compare ({selectedProducts.length}/2)
            </CompareButton>
          </div>
        </CompareBar>
      )}

      {/* Affichage de la comparaison */}
      {showComparison && selectedProducts.length === 2 && (
        <ProductComparison
          productId1={getProductId(selectedProducts[0])}
          productId2={getProductId(selectedProducts[1])}
          onClose={handleCloseComparison}
        />
      )}

      {product_description && (
        <Section>
          <DescriptionCard>
            <DescriptionTitle>
              <FiInfo size={24} />
              🌿 Main Product Description
            </DescriptionTitle>
            <DescriptionText>{product_description}</DescriptionText>
          </DescriptionCard>
        </Section>
      )}

      <Section>
        <SectionTitle>
          <FiStar size={24} />
          🌿 All Recommended Products ({recommendations?.length || 0})
        </SectionTitle>
        
        {recommendations && recommendations.length > 0 ? (
          <ProductGrid>
            {recommendations.map((product, index) => (
              <ProductCard
                key={index}
                product={product}
                showScore={true}
                showCompareButton={recommendations.length > 1}
                onCompareSelect={handleProductSelect}
                isSelectedForComparison={selectedProducts.some(p => p.name === product.name)}
              />
            ))}
          </ProductGrid>
        ) : (
          <NoResults>
            <p>🌿 No recommendations found for this search.</p>
            <p style={{ fontSize: '0.9rem', marginTop: '0.5rem', opacity: 0.8 }}>
              Try with different search criteria.
            </p>
          </NoResults>
        )}
      </Section>
    </ResultsContainer>
  );
};

export default RecommendationResults;