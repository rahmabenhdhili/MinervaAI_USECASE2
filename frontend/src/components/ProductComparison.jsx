import React, { useState } from 'react';
import styled from 'styled-components';
import { FiX, FiCheck, FiAlertCircle, FiDollarSign } from 'react-icons/fi';
import { usershopAPI } from '../utils/api';
import { normalizePriceDisplay } from '../utils/currencyUtils';

const ComparisonContainer = styled.div`
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(155, 200, 187, 0.1);
  margin: 2rem 0;
  border: 1px solid #9bc8bb;
`;

const CloseButton = styled.button`
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  cursor: pointer;
  color: #3f8872;
  font-size: 1.5rem;

  &:hover {
    color: #51ae93;
  }
`;

const Title = styled.h2`
  text-align: center;
  color: #3f8872;
  margin-bottom: 2rem;
`;

const ProductsGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
`;

const ProductCard = styled.div`
  border: 2px solid #9bc8bb;
  border-radius: 8px;
  padding: 1.5rem;
  background: #f5fefb;
`;

const ProductName = styled.h3`
  color: #51ae93;
  margin-bottom: 0.5rem;
`;

const ProductPrice = styled.div`
  font-size: 1.3rem;
  font-weight: 700;
  color: #3f8872;
  margin-bottom: 1rem;
`;

const Section = styled.div`
  margin-bottom: 1.5rem;
`;

const SectionTitle = styled.h4`
  color: #3f8872;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  text-transform: uppercase;
`;

const Text = styled.p`
  color: #3f8872;
  line-height: 1.6;
  margin-bottom: 0.5rem;
`;

const List = styled.ul`
  list-style: none;
  padding: 0;
`;

const ListItem = styled.li`
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: #3f8872;

  svg {
    margin-top: 0.2rem;
    flex-shrink: 0;
  }
`;

const MonetaryGuideSection = styled.div`
  background: linear-gradient(135deg, #51ae93 0%, #3f8872 100%);
  color: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px rgba(81, 174, 147, 0.2);
`;

const GuideTitle = styled.h3`
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
`;

const GuideItem = styled.div`
  margin-bottom: 1.5rem;

  &:last-child {
    margin-bottom: 0;
  }
`;

const GuideLabel = styled.h4`
  font-size: 1rem;
  margin-bottom: 0.5rem;
  opacity: 0.9;
`;

const GuideText = styled.p`
  line-height: 1.6;
  font-size: 1.05rem;
`;

const TechnicalGuideSection = styled.div`
  background: #f5fefb;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  border: 1px solid #9bc8bb;
`;

const RecommendationBox = styled.div`
  background: linear-gradient(135deg, #51ae93 0%, #3f8872 100%);
  color: white;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(81, 174, 147, 0.2);
`;

const RecommendationTitle = styled.h3`
  margin-bottom: 1rem;
  font-size: 1.3rem;
`;

const RecommendationProduct = styled.h2`
  font-size: 2rem;
  margin-bottom: 1rem;
`;

const LoadingSpinner = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 3rem;
  gap: 1rem;
`;

const ErrorMessage = styled.div`
  background: #fef2f2;
  color: #dc2626;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  border: 1px solid #fecaca;
`;

const ProductComparison = ({ productId1, productId2, onClose }) => {
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  React.useEffect(() => {
    if (productId1 && productId2) {
      compareProducts();
    }
  }, [productId1, productId2]);

  const compareProducts = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await usershopAPI.compare({
        product_id_1: productId1,
        product_id_2: productId2
      });
      setComparison(response.data);
    } catch (err) {
      console.error('Comparison error:', err);
      setError(err.response?.data?.detail || 'Error during comparison');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <ComparisonContainer>
        <LoadingSpinner>
          <div className="spinner" />
          <p style={{ color: '#3f8872' }}>🌿 Intelligent analysis in progress...</p>
        </LoadingSpinner>
      </ComparisonContainer>
    );
  }

  if (error) {
    return (
      <ComparisonContainer style={{ position: 'relative' }}>
        {onClose && (
          <CloseButton onClick={onClose}>
            <FiX />
          </CloseButton>
        )}
        <ErrorMessage>{error}</ErrorMessage>
      </ComparisonContainer>
    );
  }

  if (!comparison) {
    return null;
  }

  return (
    <ComparisonContainer style={{ position: 'relative' }}>
      {onClose && (
        <CloseButton onClick={onClose}>
          <FiX />
        </CloseButton>
      )}

      <Title>🌿 Intelligent AI Comparison</Title>

      {/* MONETARY GUIDE - PRIORITY */}
      <MonetaryGuideSection>
        <GuideTitle>
          <FiDollarSign size={28} />
          💰 Monetary Guide - Financial Analysis
        </GuideTitle>
        
        <GuideItem>
          <GuideLabel>💰 Price Difference</GuideLabel>
          <GuideText>{comparison.monetary_guide?.price_difference}</GuideText>
        </GuideItem>
        
        <GuideItem>
          <GuideLabel>📊 Value Analysis</GuideLabel>
          <GuideText>{comparison.monetary_guide?.value_analysis}</GuideText>
        </GuideItem>
        
        <GuideItem>
          <GuideLabel>💵 Budget Recommendation</GuideLabel>
          <GuideText>{comparison.monetary_guide?.budget_recommendation}</GuideText>
        </GuideItem>
        
        <GuideItem>
          <GuideLabel>⏳ Long-term Cost</GuideLabel>
          <GuideText>{comparison.monetary_guide?.long_term_cost}</GuideText>
        </GuideItem>
      </MonetaryGuideSection>

      {/* Product analysis */}
      <ProductsGrid>
        {/* Product 1 */}
        <ProductCard>
          <ProductName>🌿 {comparison.product_1_analysis?.product_name}</ProductName>
          <ProductPrice>{normalizePriceDisplay(comparison.product_1_analysis?.price)}</ProductPrice>
          
          <Section>
            <SectionTitle>📝 Description</SectionTitle>
            <Text>{comparison.product_1_analysis?.explanation}</Text>
          </Section>
          
          <Section>
            <SectionTitle>✅ Advantages</SectionTitle>
            <List>
              {comparison.product_1_analysis?.advantages?.map((adv, idx) => (
                <ListItem key={idx}>
                  <FiCheck color="#51ae93" />
                  <span>{adv}</span>
                </ListItem>
              ))}
            </List>
          </Section>
          
          <Section>
            <SectionTitle>⚠️ Disadvantages</SectionTitle>
            <List>
              {comparison.product_1_analysis?.disadvantages?.map((dis, idx) => (
                <ListItem key={idx}>
                  <FiAlertCircle color="#f59e0b" />
                  <span>{dis}</span>
                </ListItem>
              ))}
            </List>
          </Section>
          
          <Section>
            <SectionTitle>🎯 Best For</SectionTitle>
            <Text>{comparison.product_1_analysis?.best_for}</Text>
          </Section>
        </ProductCard>

        {/* Product 2 */}
        <ProductCard>
          <ProductName>🌿 {comparison.product_2_analysis?.product_name}</ProductName>
          <ProductPrice>{normalizePriceDisplay(comparison.product_2_analysis?.price)}</ProductPrice>
          
          <Section>
            <SectionTitle>📝 Description</SectionTitle>
            <Text>{comparison.product_2_analysis?.explanation}</Text>
          </Section>
          
          <Section>
            <SectionTitle>✅ Advantages</SectionTitle>
            <List>
              {comparison.product_2_analysis?.advantages?.map((adv, idx) => (
                <ListItem key={idx}>
                  <FiCheck color="#51ae93" />
                  <span>{adv}</span>
                </ListItem>
              ))}
            </List>
          </Section>
          
          <Section>
            <SectionTitle>⚠️ Disadvantages</SectionTitle>
            <List>
              {comparison.product_2_analysis?.disadvantages?.map((dis, idx) => (
                <ListItem key={idx}>
                  <FiAlertCircle color="#f59e0b" />
                  <span>{dis}</span>
                </ListItem>
              ))}
            </List>
          </Section>
          
          <Section>
            <SectionTitle>🎯 Best For</SectionTitle>
            <Text>{comparison.product_2_analysis?.best_for}</Text>
          </Section>
        </ProductCard>
      </ProductsGrid>

      {/* TECHNICAL GUIDE - SECONDARY */}
      <TechnicalGuideSection>
        <GuideTitle style={{ color: '#3f8872' }}>🔧 Technical Guide</GuideTitle>
        
        <GuideItem>
          <GuideLabel style={{ color: '#51ae93' }}>🏆 Quality Comparison</GuideLabel>
          <GuideText style={{ color: '#3f8872' }}>{comparison.technical_guide?.quality_comparison}</GuideText>
        </GuideItem>
        
        <GuideItem>
          <GuideLabel style={{ color: '#51ae93' }}>⚙️ Features Comparison</GuideLabel>
          <GuideText style={{ color: '#3f8872' }}>{comparison.technical_guide?.features_comparison}</GuideText>
        </GuideItem>
        
        <GuideItem>
          <GuideLabel style={{ color: '#51ae93' }}>🛡️ Durability Analysis</GuideLabel>
          <GuideText style={{ color: '#3f8872' }}>{comparison.technical_guide?.durability_analysis}</GuideText>
        </GuideItem>
        
        <GuideItem>
          <GuideLabel style={{ color: '#51ae93' }}>📈 Performance Rating</GuideLabel>
          <GuideText style={{ color: '#3f8872' }}>{comparison.technical_guide?.performance_rating}</GuideText>
        </GuideItem>
      </TechnicalGuideSection>

      {/* Final recommendation */}
      <RecommendationBox>
        <RecommendationTitle>🏆 Final Recommendation</RecommendationTitle>
        <RecommendationProduct>🌿 {comparison.final_recommendation}</RecommendationProduct>
        <GuideText style={{ color: 'white', fontSize: '1.1rem' }}>
          {comparison.recommendation_reason}
        </GuideText>
      </RecommendationBox>
    </ComparisonContainer>
  );
};

export default ProductComparison;