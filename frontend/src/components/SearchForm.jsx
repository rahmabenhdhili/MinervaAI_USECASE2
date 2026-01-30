import React, { useState } from 'react';
import styled from 'styled-components';
import { FiSearch, FiTag, FiFolder, FiDollarSign } from 'react-icons/fi';
import { BiCategory, BiSort } from 'react-icons/bi';
import { MdDescription } from 'react-icons/md';

const FormContainer = styled.div`
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(155, 200, 187, 0.1);
  margin-bottom: 2rem;
  border: 1px solid #9bc8bb;
`;

const Title = styled.h2`
  margin-bottom: 1.5rem;
  color: #3f8872;
  text-align: center;
`;

const Form = styled.form`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
`;

const InputGroup = styled.div`
  display: flex;
  flex-direction: column;
`;

const Label = styled.label`
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #3f8872;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  svg {
    color: #51ae93;
  }
`;

const Input = styled.input`
  padding: 12px;
  border: 2px solid #9bc8bb;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s ease;

  &:focus {
    outline: none;
    border-color: #51ae93;
  }
`;

const Select = styled.select`
  padding: 12px;
  border: 2px solid #9bc8bb;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s ease;

  &:focus {
    outline: none;
    border-color: #51ae93;
  }
`;

const TextArea = styled.textarea`
  padding: 12px;
  border: 2px solid #9bc8bb;
  border-radius: 8px;
  font-size: 16px;
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.3s ease;

  &:focus {
    outline: none;
    border-color: #51ae93;
  }
`;

const SearchButton = styled.button`
  background: linear-gradient(135deg, #3f8872 0%, #51ae93 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(63, 136, 114, 0.3);
    background: linear-gradient(135deg, #51ae93 0%, #88c695 100%);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const SearchForm = ({ onSearch, loading }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    min_price: '',
    max_price: '',
    sort_by: 'relevance'
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Check that at least one field is filled
    const hasData = formData.name || formData.description || formData.category || formData.min_price || formData.max_price;
    
    if (!hasData) {
      alert('Please fill in at least one search field');
      return;
    }

    // Prepare data with price conversion
    const searchData = {
      query: formData.name || formData.description || undefined, // Use name or description as main query
      name: formData.name || undefined,
      description: formData.description || undefined,
      category: formData.category || undefined,
      min_price: formData.min_price ? parseFloat(formData.min_price) : undefined,
      max_price: formData.max_price ? parseFloat(formData.max_price) : undefined,
      sort_by: formData.sort_by || 'relevance'
    };

    // Validate prices
    if (searchData.min_price && searchData.max_price && searchData.min_price > searchData.max_price) {
      alert('Minimum price cannot be higher than maximum price');
      return;
    }

    onSearch(searchData);
  };

  return (
    <FormContainer>
      <Form onSubmit={handleSubmit}>
        <InputGroup>
          <Label htmlFor="name">
            <FiTag size={16} />
            Product Name
          </Label>
          <Input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Ex: smartphone, sofa, shoes..."
          />
        </InputGroup>

        <InputGroup>
          <Label htmlFor="category">
            <BiCategory size={16} />
            Category
          </Label>
          <Input
            type="text"
            id="category"
            name="category"
            value={formData.category}
            onChange={handleChange}
            placeholder="Ex: Electronics, Furniture, Shoes..."
          />
        </InputGroup>

        <InputGroup>
          <Label htmlFor="min_price">
            <FiDollarSign size={16} />
            Minimum Price (TND)
          </Label>
          <Input
            type="number"
            id="min_price"
            name="min_price"
            value={formData.min_price}
            onChange={handleChange}
            placeholder="Ex: 20"
            min="0"
            step="0.01"
          />
        </InputGroup>

        <InputGroup>
          <Label htmlFor="max_price">
            <FiDollarSign size={16} />
            Maximum Price (TND)
          </Label>
          <Input
            type="number"
            id="max_price"
            name="max_price"
            value={formData.max_price}
            onChange={handleChange}
            placeholder="Ex: 100"
            min="0"
            step="0.01"
          />
        </InputGroup>

        <InputGroup>
          <Label htmlFor="sort_by">
            <BiSort size={16} />
            Sort By
          </Label>
          <Select
            id="sort_by"
            name="sort_by"
            value={formData.sort_by}
            onChange={handleChange}
          >
            <option value="relevance">Relevance (Score)</option>
            <option value="price_asc">Price Ascending</option>
            <option value="price_desc">Price Descending</option>
          </Select>
        </InputGroup>

        <InputGroup style={{ gridColumn: '1 / -1' }}>
          <Label htmlFor="description">
            <MdDescription size={16} />
            Short Description
          </Label>
          <TextArea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Describe the type of product you are looking for..."
          />
        </InputGroup>
      </Form>

      <SearchButton type="submit" onClick={handleSubmit} disabled={loading}>
        {loading ? (
          <>
            <div className="spinner" style={{ width: '20px', height: '20px' }} />
            Searching...
          </>
        ) : (
          <>
            <FiSearch size={20} />
            Search and Get Recommendations
          </>
        )}
      </SearchButton>
    </FormContainer>
  );
};

export default SearchForm;