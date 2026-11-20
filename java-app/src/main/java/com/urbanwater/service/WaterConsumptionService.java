package com.urbanwater.service;

import com.urbanwater.model.WaterConsumption;
import com.urbanwater.repository.WaterConsumptionRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@Service
public class WaterConsumptionService {

    private final WaterConsumptionRepository repository;

    public WaterConsumptionService(WaterConsumptionRepository repository) {
        this.repository = repository;
    }

    public WaterConsumption create(WaterConsumption record) {
        return repository.save(record);
    }

    public List<WaterConsumption> findAll() {
        return repository.findAll();
    }

    public WaterConsumption findById(Long id) {
        return repository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "Water consumption record not found: " + id
                ));
    }

    public WaterConsumption update(Long id, WaterConsumption record) {
        boolean updated = repository.update(id, record);

        if (!updated) {
            throw new ResponseStatusException(
                    HttpStatus.NOT_FOUND,
                    "Water consumption record not found: " + id
            );
        }

        return findById(id);
    }

    public void delete(Long id) {
        boolean deleted = repository.delete(id);

        if (!deleted) {
            throw new ResponseStatusException(
                    HttpStatus.NOT_FOUND,
                    "Water consumption record not found: " + id
            );
        }
    }
}
