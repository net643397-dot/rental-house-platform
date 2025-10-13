-- 为house_info表添加经纬度字段
ALTER TABLE `house_info`
ADD COLUMN `latitude` DECIMAL(10, 8) NULL DEFAULT NULL COMMENT '纬度' AFTER `house_num`,
ADD COLUMN `longitude` DECIMAL(11, 8) NULL DEFAULT NULL COMMENT '经度' AFTER `latitude`;

-- 为经纬度字段创建索引，便于地理位置搜索
CREATE INDEX `idx_location` ON `house_info` (`latitude`, `longitude`);