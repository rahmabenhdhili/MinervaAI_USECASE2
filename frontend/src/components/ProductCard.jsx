import React from 'react';
import styled from 'styled-components';
import { FiExternalLink, FiTag } from 'react-icons/fi';
import { TbCurrencyDinar } from 'react-icons/tb';
import { normalizePriceDisplay } from '../utils/currencyUtils';

const Card = styled.div`
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(155, 200, 187, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
  border: 1px solid #9bc8bb;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(155, 200, 187, 0.15);
    border-color: #51ae93;
  }
`;

const ImageContainer = styled.div`
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: #f5fefb;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const ProductImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;

  ${Card}:hover & {
    transform: scale(1.05);
  }
`;

const ImagePlaceholder = styled.div`
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #f5fefb 0%, #b2d0ab 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3f8872;
  font-size: 14px;
`;

const Content = styled.div`
  padding: 1.5rem;
`;

const ProductName = styled.h3`
  margin-bottom: 0.5rem;
  color: #3f8872;
  font-size: 1.1rem;
  line-height: 1.4;
`;

const ProductInfo = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
`;

const InfoTag = styled.span`
  display: flex;
  align-items: center;
  gap: 4px;
  background: #f5fefb;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.85rem;
  color: #3f8872;
  border: 1px solid #9bc8bb;
`;

const Price = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 1.1rem;
  font-weight: 600;
  color: #51ae93;
  margin-bottom: 1rem;
`;

const ActionButton = styled.a`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #51ae93 0%, #3f8872 100%);
  color: white;
  text-decoration: none;
  padding: 10px 16px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(81, 174, 147, 0.3);
  }
`;

const CompareButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: ${props => props.selected ? '#3f8872' : '#f5fefb'};
  color: ${props => props.selected ? 'white' : '#3f8872'};
  border: 2px solid ${props => props.selected ? '#3f8872' : '#9bc8bb'};
  padding: 10px 16px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 0.5rem;
  width: 100%;

  &:hover {
    transform: translateY(-2px);
    background: ${props => props.selected ? '#51ae93' : '#b2d0ab'};
    border-color: ${props => props.selected ? '#51ae93' : '#51ae93'};
  }
`;

const ProductCard = ({ 
  product, 
  showScore = true, 
  onCompareSelect, 
  isSelectedForComparison = false, 
  showCompareButton = false 
}) => {
  const handleImageError = (e) => {
    e.target.style.display = 'none';
  };

  return (
    <Card>
      <ImageContainer>
        {product.img ? (
          <ProductImage
            src={product.img}
            alt={product.name}
            onError={handleImageError}
          />
        ) : (
          <ImagePlaceholder>🌿 Image not available</ImagePlaceholder>
        )}
      </ImageContainer>
      
      <Content>
        <ProductName>{product.name}</ProductName>
        
        <ProductInfo>
          <InfoTag>
            <FiTag size={14} />
            {product.category}
          </InfoTag>
          <InfoTag>{product.brand}</InfoTag>
          {showScore && product.score !== undefined && product.score !== null && (
            <InfoTag style={{ background: '#b2d0ab', color: '#3f8872', fontWeight: '600' }}>
              ⭐ Score: {product.score.toFixed(2)}
            </InfoTag>
          )}
        </ProductInfo>

        <Price>
          <TbCurrencyDinar size={18} />
          {normalizePriceDisplay(product.price)}
        </Price>

        <ActionButton
          href={product.url}
          target="_blank"
          rel="noopener noreferrer"
        >
          <FiExternalLink size={16} />
          View Product
        </ActionButton>

        {showCompareButton && onCompareSelect && (
          <CompareButton
            selected={isSelectedForComparison}
            onClick={() => onCompareSelect(product)}
          >
            {isSelectedForComparison ? '✓ Selected' : '⚖️ Compare'}
          </CompareButton>
        )}
      </Content>
    </Card>
  );
};

export default ProductCard;